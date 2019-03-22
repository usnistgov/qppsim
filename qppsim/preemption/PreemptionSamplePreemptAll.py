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
Module with a simple Pre-emption implementation.
"""

import qppsim.Amc
import qppsim.Des
import qppsim.BearerList
import qppsim.preemption.PreemptionBase


class PreemptionSamplePreemptAll(qppsim.preemption.PreemptionBase.PreemptionBase):
    """
    Class for a sample Pre-emption implementation. This implementation selects
    all the bearers with a lower ARP than the bearer that needs to be accepted
    and pre-empts all of them.
    """
    def attempt_preemption(self, new_bearer_id, new_bearer_arp, rbs_needed, rbs_used):
        """
        Attempt to pre-empt bearers to free resources for a new bearer. This
        implementation selects all the bearers with a lower ARP than the bearer
        that needs to be accepted, and pre-empts all of them.
        """
        success = False
        preempted = []
        candidates = []
        bearer_list = qppsim.BearerList.get_bearer_list().bearers
        for ue in bearer_list:
            for bid in bearer_list[ue]:
                bearer = bearer_list[ue][bid]
                if bearer.pvi and bearer.qci < 5 and bearer.arp > new_bearer_arp:
                    candidates.append(
                        [bearer, qppsim.Amc.get_rbs_for_rate(
                            bearer.ue.mcs, bearer.gbr)])
        current_rbs_used = rbs_used
        for candidate in candidates:
            preempted.append(candidate)
            current_rbs_used -= candidate[1][1]
        success = (current_rbs_used + rbs_needed <= 50000)

        if not success:
            preempted.clear()
        else:
            for bearer in preempted:
                qppsim.Des.get_des().trace_writer.trace_arp_preemption(
                    qppsim.Des.get_des().now(), bearer[0].ue.imsi,
                    bearer[0].bid, bearer[1][1], bearer[0].qci,
                    bearer[0].gbr, bearer[0].arp, bearer[0].pvi, bearer[0].pci)

        return success, preempted

    def qos_preemption(self, ue_imsi, bearer_id, bearer_arp):
        """
        Attempt to pre-empt a bearer to ensure that the specified bearer can
        comply with its QoS contract.
        """
        success = False
        preempted = []
        candidates = []
        bearer_list = qppsim.BearerList.get_bearer_list().bearers
        for ue in bearer_list:
            for bid in bearer_list[ue]:
                bearer = bearer_list[ue][bid]
                if bearer.pvi and bearer.qci < 5 and bearer.arp > bearer_arp:
                    candidates.append(
                        [bearer, qppsim.Amc.get_rbs_for_rate(
                            bearer.ue.mcs, bearer.gbr)])
        for candidate in candidates:
            preempted.append(candidate)
        success = len(candidates) > 0

        if not success:
            preempted.clear()
        else:
            for bearer in preempted:
                qppsim.Des.get_des().trace_writer.trace_arp_preemption(
                    qppsim.Des.get_des().now(), bearer[0].ue.imsi,
                    bearer[0].bid, bearer[1][1], bearer[0].qci,
                    bearer[0].gbr, bearer[0].arp, bearer[0].pvi, bearer[0].pci)

        return success, preempted
