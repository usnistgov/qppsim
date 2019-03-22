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
Implementation of the Access Control module that only traces the request and
accepts all the bearers.
"""

import qppsim.accesscontrol.AccessControlBase
import qppsim.Des


class AccessControlTraceOnly(qppsim.accesscontrol.AccessControlBase.AccessControlBase):
    """
    Implementation of the Access Control module that only traces the request
    and accepts all the bearers.
    """
    def check_bearer_activation(self, gbr, mbr, qci, arp, pvi, pci,
                                imsi, bid, mcs):
        """
        Trace the request to activate a bearer, and accept all bearers (tracing
        the response).
        """
        des = qppsim.Des.get_des()
        current_time = des.now()
        des.trace_writer.trace_arp_activation_check(
            current_time, imsi, self.get_needed_gbr_rbs(gbr, mcs, qci),
            self.get_used_gbr_rbs(), qci, gbr,
            arp, pvi, pci)
        des.trace_writer.trace_arp_activation_result(
            current_time, imsi, "ACCEPT",
            self.get_needed_gbr_rbs(gbr, mcs, qci),
            self.get_used_gbr_rbs(), qci, gbr,
            arp, pvi, pci)

        return True

    def check_bearer_modification(self, old_gbr, old_qci,
                                  new_gbr, new_mbr, new_qci,
                                  arp, pvi, pci, imsi, bid, mcs):
        """
        Trace the request to modify the QoS of a bearer, and accept all bearers
        (tracing the response).
        """
        des = qppsim.Des.get_des()
        current_time = des.now()

        needed_old_rbs = self.get_needed_gbr_rbs(old_gbr, mcs, old_qci)
        needed_new_rbs = self.get_needed_gbr_rbs(new_gbr, mcs, new_qci)
        used_rbs = self.get_used_gbr_rbs()
        des.trace_writer.trace_arp_modification_check(
            current_time, imsi, needed_old_rbs, needed_new_rbs, used_rbs,
            old_qci, old_gbr, new_qci, new_gbr, arp, pvi, pci)
        des.trace_writer.trace_arp_modification_result(
            current_time, imsi, "ACCEPT", needed_old_rbs, needed_new_rbs,
            used_rbs, new_qci, new_gbr, arp, pvi, pci)
