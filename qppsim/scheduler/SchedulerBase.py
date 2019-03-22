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
Module with the base class for the Schedulers. It also defines the delay for
attempting retransmission for the RBs that failed.
"""
from abc import ABCMeta, abstractmethod

import qppsim.Amc
import qppsim.Des
import qppsim.Time

#: Amount of milliseconds to wait before attempting to retransmit a failed
#: transmission
RTX_DELAY = qppsim.Time.Time(milliseconds=8)


class SchedulerBase(metaclass=ABCMeta):
    """
    Base class for the schedulers. Provides a basic constructor that must be
    called by the subclasses, a dictionary with the RBs that need retransmission
    sorted by the time at which they will be retransmitted, a method to process
    the RBs to retransmit in the current TTI, a method to process the allocations
    made, a method to transmit RBs that were awaiting retransmission, and a method
    to put back in the retransmission queue RBs that were awaiting retransmission
    and their TX failed again.

    It defines the 'schedule' method, that actually holds the scheduler logic,
    but provides no implementation.
    """
    def __init__(self, num_rbs):
        """
        Constructor that initializes the dictionary of RBs pending to retransmit,
        sets the total number of RBs to allocate in each TTI, and sets the initial
        value for the last time the QoS of the bearers was checked.
        """
        self.__rtx_pending = {}
        self.__num_rbs = num_rbs
        self.__last_qos_check = qppsim.Time.Time(-float('inf'))

    @property
    def num_rbs(self):
        """
        Get the total number of RBs to allocate in each TTI
        """
        return self.__num_rbs

    @property
    def rtx_pending(self):
        """
        Get the dictionary with the RBs pending retransmission.
        """
        return self.__rtx_pending

    @property
    def last_qos_check(self):
        """
        Get the last time when the bearers QoS was checked.
        """
        return self.__last_qos_check

    @last_qos_check.setter
    def last_qos_check(self, last_qos_check):
        """
        Set the last time when the bearers QoS was checked.
        """
        self.__last_qos_check = last_qos_check

    @abstractmethod
    def schedule(self):
        """
        Method that holds the logic of the scheduler and provides the allocation
        for a TTI. Each subclass must include the following steps in this method:
            - Get the current time from the DES
            - Get the list of active bearers
            - Add an event for the next scheduling event, at current_time + 1
            - If needed, check the QoS of the bearers
            - Process the retransmissions for the current TTI calling
                'process_retransmissions'
            - Allocate the remaining RBs according to the scheduler logic
            - Process the allocation by calling 'process_allocations'

        Not implemented
        """
        pass

    def process_retransmissions(self, current_time, bearers):
        """
        Process the RBs that need to be retransmitted in this TTI. If this is the
        4th retransmission, assume automatic TX success. Otherwise, check with the
        DES, and either transmit the RBs, or put them back in the 'awaiting
        retransmission' queue, with an updated time to attempt retransmission.
        """
        used_rbs = 0
        idx_time = current_time
        if idx_time in self.__rtx_pending:
            for ue in self.__rtx_pending[idx_time]:
                for bid in self.__rtx_pending[idx_time][ue]:
                    while self.__rtx_pending[idx_time][ue][bid]:
                        (rbs, tbs, num_rtx) = self.__rtx_pending[idx_time][ue][bid].pop(0)
                        used_rbs += rbs
                        if num_rtx == 4:
                            # Max RTX reached. Assume success
                            self.tx_from_rtx(bearers, ue, bid, tbs)
                        else:
                            # Check if the transmission fails again
                            if qppsim.Des.get_des().get_tx_success():
                                # TX success
                                self.tx_from_rtx(bearers, ue, bid, tbs)
                            else:
                                # TX failed
                                self.rtx(idx_time, ue, bid, rbs, tbs, num_rtx)
            del self.__rtx_pending[idx_time]
        return used_rbs

    def process_allocations(self, allocations, bearers):
        """
        Process the allocations for this TTI. For each bearer allocation, check
        with the DES, if the transmission succeeds, and either transmit the RBs,
        or put them in the 'awaiting retransmission' queue, with the time
        at which to attempt retransmission.
        """
        for ue in allocations:
            for bid in allocations[ue]:
                num_rbs = allocations[ue][bid]
                tbs = qppsim.Amc.TBS_FOR_MCS[ue.mcs][num_rbs]
                # Try to transmit the allocated RBs
                if qppsim.Des.get_des().get_tx_success():
                    bearers[ue][bid].tx(tbs, rtx=False)
                else:
                    bearers[ue][bid].tx(tbs, rtx=True)
                    self.rtx(qppsim.Des.get_des().now(), ue, bid, num_rbs, tbs, 0)

    def tx_from_rtx(self, bearers, ue, bid, tbs):
        """
        Transmit a certain amount of bytes from the 'awaiting retransmission'
        queue in a bearer.
        """
        # Make sure the bearer is still active
        if ue in bearers and bid in bearers[ue]:
            bearers[ue][bid].rtx(tbs)

    def rtx(self, current_time, ue, bid, rbs, tbs, num_rtx):
        """
        Add a number of RBs to the 'awaiting retransmission' queue.
        """
        rtx_time = current_time + RTX_DELAY
        if rtx_time not in self.__rtx_pending:
            self.__rtx_pending[rtx_time] = {}
        if ue not in self.__rtx_pending[rtx_time]:
            self.__rtx_pending[rtx_time][ue] = {}
        if bid not in self.__rtx_pending[rtx_time][ue]:
            self.__rtx_pending[rtx_time][ue][bid] = []
        self.__rtx_pending[rtx_time][ue][bid].append((rbs, tbs, num_rtx + 1))
