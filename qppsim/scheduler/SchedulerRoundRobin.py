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
Module with a Round-Robin Scheduler. It follows the logic of the NistRR scheduler
in ns-3
"""

import qppsim.Amc
import qppsim.BearerList
import qppsim.Des
import qppsim.Event
import qppsim.Time
import qppsim.scheduler.SchedulerBase


class SchedulerRoundRobin(qppsim.scheduler.SchedulerBase.SchedulerBase):
    """
    Class with an implementation of a Round-Robin scheduler.
    """
    def __init__(self, num_rbs):
        """
        Constructor that extends the parent's constructor by adding references
        to the last UE and last BID that were allocated.
        """
        super().__init__(num_rbs)
        self.__last_ue = None
        self.__last_bid = None

    def schedule(self):
        """
        Method that holds the logic of the scheduler and provides the allocation
        for a TTI. The steps followed are:
            - Get the current time from the DES
            - Get the list of active bearers
            - Add an event for the next scheduling event, at current_time + 1
            - If needed, check the QoS of the bearers
            - Process the retransmissions for the current TTI calling the parent's
                'process_retransmissions'
            - Locate the last UE and BID allocated. If they cannot be located,
                roll back to the first bearer in the UE, or first UE in the list.
            - Allocate RBs one by one to the bearers that have data pending to
                transmit, in a Round-Robin fashion, until we run out of RBs or
                there are no more bearers with data to transmit.
            - Allocate the remaining RBs according to the scheduler logic
            - Process the allocation by calling the parent's 'process_allocations'
        """
        des = qppsim.Des.get_des()
        # Get info from the DES and the bearer list
        current_time = qppsim.Des.get_des().now()
        bearers = qppsim.BearerList.get_bearer_list().bearers
        # First schedule the next scheduler event
        des.add_event(qppsim.Event.Event(des.now() + qppsim.Time.ONE_MILLISECOND, self, self.schedule, []))
        # Then get the Bearers' QoS metrics
        if current_time >= self.last_qos_check + des.qos_monitor_interval:
            bearer_qos = des.qos_monitor.get_qos()
            self.last_qos_check = current_time

        # Now do the scheduling
        # First the retransmissions
        available_rbs = super().num_rbs - self.process_retransmissions(current_time, bearers)
        # Now allocate in RR order.
        # First, figure out where we left last time
        # If this is the first time, we start from the beginning of the bearer list map
        try:
            ue_idx = bearers.index(self.__last_ue)
        except ValueError:
            self.__last_ue = bearers.iloc[0]
            self.__last_bid = bearers[self.__last_ue].iloc[0]
            ue_idx = 0

        try:
            bearer_idx = bearers[self.__last_ue].index(self.__last_bid)
        except ValueError:
            self.__last_bid = bearers[self.__last_ue].iloc[0]
            bearer_idx = 0

        allocations = {}
        ue_tmp = bearers.iloc[ue_idx]
        bid_tmp = bearers[ue_tmp].iloc[bearer_idx]
        while available_rbs > 0:
            # Now we know who's next
            if ue_tmp in allocations and bid_tmp in allocations[ue_tmp]:
                bytes_out = qppsim.Amc.TBS_FOR_MCS[ue_tmp.mcs][allocations[ue_tmp][bid_tmp]]
            else:
                bytes_out = 0
            if bearers[ue_tmp][bid_tmp].pending_size() - bytes_out > 0:
                if ue_tmp not in allocations:
                    allocations[ue_tmp] = {}
                if bid_tmp not in allocations[ue_tmp]:
                    allocations[ue_tmp][bid_tmp] = 0
                allocations[ue_tmp][bid_tmp] += 1

                self.__last_ue = ue_tmp
                self.__last_bid = bid_tmp
                available_rbs -= 1

            bearer_idx = (bearer_idx + 1) % len(bearers[ue_tmp])
            if bearer_idx == 0:
                ue_idx = (ue_idx + 1) % len(bearers)
                ue_tmp = bearers.iloc[ue_idx]
            bid_tmp = bearers[ue_tmp].iloc[bearer_idx]

            # Check if we have gone through all the bearers and not being able to allocate any
            if ue_tmp == self.__last_ue and bid_tmp == self.__last_bid:
                if ue_tmp in allocations and bid_tmp in allocations[ue_tmp]:
                    bytes_out = qppsim.Amc.TBS_FOR_MCS[ue_tmp.mcs][allocations[ue_tmp][bid_tmp]]
                else:
                    bytes_out = 0
                if bearers[ue_tmp][bid_tmp].pending_size() - bytes_out <= 0:
                    break

        self.process_allocations(allocations, bearers)
