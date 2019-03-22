# -*- coding: utf-8 -*-
#
# NIST-developed software is provided by NIST as a public service. You may
# use, copy and distribute copies of the software in any medium, provided that
# you keep intact this entire notice. You may improve, modify and create
# derivative works of the software or any portion of the software, and you may
# copy and distribute such modifications or works. Modified works should carry
# a notice stating that you changed the software and should note the date and
# nature of any such change. Please explicitly acknowledge the National
# Institute of Standards and Technology as the source of the software.
#
# NIST-developed software is expressly provided "AS IS." NIST MAKES NO
# WARRANTY OF ANY KIND, EXPRESS, IMPLIED, IN FACT OR ARISING BY OPERATION OF
# LAW, INCLUDING, WITHOUT LIMITATION, THE IMPLIED WARRANTY OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE, NON-INFRINGEMENT AND DATA ACCURACY. NIST
# NEITHER REPRESENTS NOR WARRANTS THAT THE OPERATION OF THE SOFTWARE WILL BE
# UNINTERRUPTED OR ERROR-FREE, OR THAT ANY DEFECTS WILL BE CORRECTED. NIST
# DOES NOT WARRANT OR MAKE ANY REPRESENTATIONS REGARDING THE USE OF THE
# SOFTWARE OR THE RESULTS THEREOF, INCLUDING BUT NOT LIMITED TO THE
# CORRECTNESS, ACCURACY, RELIABILITY, OR USEFULNESS OF THE SOFTWARE.
#
# You are solely responsible for determining the appropriateness of using and
# distributing the software and you assume all risks associated with its use,
# including but not limited to the risks and costs of program errors,
# compliance with applicable laws, damage to or loss of data, programs or
# equipment, and the unavailability or interruption of operation. This
# software is not intended to be used in any situation where a failure could
# cause risk of injury or damage to property. The software developed by NIST
# employees is not subject to copyright protection within the United States.

"""
Implementation of the Access Control module with a basic behavior.
"""

import qppsim.accesscontrol.AccessControlBase
import qppsim.Des


class AccessControlSample(qppsim.accesscontrol.AccessControlBase.AccessControlBase):
    """
    Sample implementation of the Access Control module with a basic behavior.

    When checking if a bearer can be activated, if the result of the check is
    negative this implementation calls the Pre-emption module to try free RBS.
    If the Pre-emption module succeeds, this class deactivates the bearers
    indicated by that module, and proceeds to accept the bearer that was
    being tested.
    """
    def check_bearer_activation(self, gbr, mbr, qci, arp, pvi, pci,
                                imsi, bid, mcs):
        """
        Check if a given bearer can be admitted in the network and return a
        boolean with the result of the check.

        The check process returns True if:
            - The bearer is not GBR (based on the QCI).
            - The bearer is GBR but there are enough resources to provide the
              required GBR at the MCS of the UE.
            - The bearer is GBR, there are not enough resources to provide the
              GBR at the MCS of the UE, but the pre-emption module managed to
              find bearers that can be pre-empted to free enough resources.
        In the last case, the bearers indicated by the pre-emption module are
        deactivated before the result is returned.

        Whatever the result of the check, the TraceWriter module is called to
        trace it if appropriate.
        """
        des = qppsim.Des.get_des()
        current_time = des.now()

        needed_rbs = self.get_needed_gbr_rbs(gbr, mcs, qci)
        used_rbs = self.get_used_gbr_rbs()
        des.trace_writer.trace_arp_activation_check(
            current_time, imsi, needed_rbs, used_rbs, qci, gbr,
            arp, pvi, pci)

        success = (qci > 5) or (used_rbs + needed_rbs <= super().num_rbs * 1000)
        if success:
            des.trace_writer.trace_arp_activation_result(
                current_time, imsi, "ACCEPT",
                self.get_needed_gbr_rbs(gbr, mcs, qci),
                self.get_used_gbr_rbs(), qci, gbr, arp, pvi, pci)
        else:
            des.trace_writer.trace_arp_activation_result(
                current_time, imsi, "DENIED",
                needed_rbs, used_rbs, qci, gbr, arp, pvi, pci)
            # Try Pre-emption
            if pci:
                (success, preempted) = des.preemption_policy.attempt_preemption(
                    bid, arp, needed_rbs, used_rbs)
                if success:
                    for preempted_info in preempted:
                        bearer = preempted_info[0]
                        self.bearer_deactivation(bearer)
                        bearer.teardown()
                    des.trace_writer.trace_arp_activation_result(
                        current_time, imsi, "ACCEPT",
                        needed_rbs, used_rbs, qci, gbr, arp, pvi, pci)
                else:
                    des.trace_writer.trace_arp_activation_result(
                        current_time, imsi, "DENIED",
                        needed_rbs, used_rbs, qci, gbr, arp, pvi, pci)
        return success

    def check_bearer_modification(self, old_gbr, old_qci,
                                  new_gbr, new_mbr, new_qci,
                                  arp, pvi, pci, imsi, bid, mcs):
        """
        Return a boolean stating if a bearer can be modified from the old GBR
        and QCI to the new provided GBR, MBR, QCI, and MCS. ARP, PCI, and / or
        PVI modifications are not allowed at this moment

        The check process returns True if:
            - The new QCI is not GBR.
            - The new QCI is GBR but the new GBR is less or equal than the old
              GBR.
            - The new QCI is GBR, there are not enough resources to provide the
              GBR at the MCS of the UE, but the pre-emption module managed to
              find bearers that can be pre-empted to free enough resources.
        In the last case, the bearers indicated by the pre-emption module are
        deactivated before the result is returned.

        Whatever the result of the check, the TraceWriter module is called to
        trace it if appropriate.
        """
        des = qppsim.Des.get_des()
        current_time = des.now()

        needed_old_rbs = self.get_needed_gbr_rbs(old_gbr, mcs, old_qci)
        needed_new_rbs = self.get_needed_gbr_rbs(new_gbr, mcs, new_qci)
        needed_rbs = needed_new_rbs - needed_old_rbs
        used_rbs = self.get_used_gbr_rbs()
        des.trace_writer.trace_arp_modification_check(
            current_time, imsi, needed_old_rbs, needed_new_rbs, used_rbs,
            old_qci, old_gbr, new_qci, new_gbr, arp, pvi, pci)

        success = (new_qci > 5) or \
            (new_gbr <= old_gbr) or \
            (used_rbs + needed_rbs <= super().num_rbs * 1000)
        if success:
            des.trace_writer.trace_arp_modification_result(
                current_time, imsi, "ACCEPT", needed_old_rbs, needed_new_rbs,
                used_rbs, new_qci, new_gbr, arp, pvi, pci)
        else:
            des.trace_writer.trace_arp_modification_result(
                current_time, imsi, "DENIED", needed_old_rbs, needed_new_rbs,
                used_rbs, new_qci, new_gbr, arp, pvi, pci)
            # Try Pre-emption
            if pci:
                (success, preempted) = des.preemption_policy.attempt_preemption(
                    bid, arp, needed_rbs, used_rbs)
                if success:
                    for preempted_info in preempted:
                        bearer = preempted_info[0]
                        self.bearer_deactivation(bearer)
                        bearer.teardown()
                    des.trace_writer.trace_arp_modification_result(
                        current_time, imsi, "ACCEPT", needed_old_rbs, needed_new_rbs,
                        used_rbs, new_qci, new_gbr, arp, pvi, pci)
                else:
                    des.trace_writer.trace_arp_modification_result(
                        current_time, imsi, "DENIED", needed_old_rbs, needed_new_rbs,
                        used_rbs, new_qci, new_gbr, arp, pvi, pci)
        return success
