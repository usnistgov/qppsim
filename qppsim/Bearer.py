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
Module that provides the model for a Bearer
"""

import collections

import sortedcontainers

import qppsim.Des
import qppsim.Event
import qppsim.Time
import qppsim.qosmonitor.QosMonitorBase


TX_DELAY = qppsim.Time.Time(milliseconds=4)
"""
Constant with the TX delay to add to a packet reception once the last byte has
been successfully scheduled
"""


QosTuple = collections.namedtuple('QoSTuple', 'min avg max last')
"""
Named tuple to allow for easier access to the content of the QoS fields
"""


class Bearer:
    """
    Class providing the model for Bearers. It includes the QoS and ARP configuration
    of the bearer, a reference to the UE that activates the Bearer, the size of the
    RLC queue for the Bearer, and the port used by the application linked to this
    bearer (used only for tracing purposes).

    A bearer may be dedicated, or default. Dedicated bearers are linked to
    application instances in a 1-to-1 relation. Default bearers may have 0 to n
    application instances linked to them, and therefore their 'port' member is set
    to 'None'.

    The class is hashable and comparable.
    """
    def __init__(self, ue, qci, gbr, mbr, pvi, pci, arp, queue_size, port):
        """
        Constructor, receiving the UE that establishes the bearer, the QCI,
        GBR and MBR rates, PCI and PCI flags, ARP, RLC queue size (in bytes),
        and the Port of the application associated with this bearer (or 'None'
        if this is a default bearer)

        The QCI is used to compute the priority using the dictionary in the
        QosMonitorBase.

        Empty SortedDicts are initialized to store loss and throughput
        measurements.

        The bearer activation is traced in the bearer trace.
        """
        self._ue = ue
        self._bid = self._ue.get_bid()
        self._qci = qci
        self._gbr = gbr
        self._mbr = mbr
        self._pvi = pvi
        self._pci = pci
        self._arp = arp
        self._queue_size = queue_size
        self._queue = []
        self._mcs = ue.mcs
        self._port = port
        self._priority = qppsim.qosmonitor.QosMonitorBase.QOS_LIMITS_PER_QCI[qci][1]
        self._loss = sortedcontainers.SortedDict()
        self._throughput = sortedcontainers.SortedDict()
        qppsim.Des.get_des().trace_writer.trace_bearer(
            qppsim.Des.get_des().now(), "ACTIVATION", self._ue.imsi,
            self._bid, self._qci, self._port)

    @property
    def ue(self):
        """
        Return the UE that established this bearer
        """
        return self._ue

    @property
    def bid(self):
        """
        Return the Bearer ID
        """
        return self._bid

    @property
    def qci(self):
        """
        Return the QCI
        """
        return self._qci

    @qci.setter
    def qci(self, qci):
        """
        Set the QCI
        """
        self._qci = qci

    @property
    def gbr(self):
        """
        Return the GBR
        """
        return self._gbr

    @gbr.setter
    def gbr(self, gbr):
        """
        Set the GBR
        """
        self._gbr = gbr

    @property
    def mbr(self):
        """
        Get the MBR
        """
        return self._mbr

    @mbr.setter
    def mbr(self, mbr):
        """
        Set the MBR
        """
        self._mbr = mbr

    @property
    def pvi(self):
        """
        Get the PVI
        """
        return self._pvi

    @pvi.setter
    def pvi(self, pvi):
        """
        Set the PVI
        """
        self._pvi = pvi

    @property
    def pci(self):
        """
        Get the PCI
        """
        return self._pci

    @pci.setter
    def pci(self, pci):
        """
        Set the PCI
        """
        self._pci = pci

    @property
    def arp(self):
        """
        Get the ARP
        """
        return self._arp

    @arp.setter
    def arp(self, arp):
        """
        Set the ARP
        """
        self._arp = arp

    @property
    def queue_size(self):
        """
        Get the RLC queue size, in bytes
        """
        return self._queue_size

    @property
    def mcs(self):
        """
        Get the UE MCS
        """
        return self._mcs

    @property
    def port(self):
        """
        Get the Port used by the application
        """
        return self._port

    def __str__(self):
        """
        Return the string representation of the Bearer
        """
        return ("Bearer {0.bid} (IMSI {0.ue.imsi}): QCI {0.qci}\tGBR {0.gbr}" +
                "\tMBR {0.mbr}\tPVI {0.pvi}\tPCI {0.pci}\tARP {0.arp}" +
                "\tQueue Size {0.queue_size}\tMCS {0.mcs}\tPort {0.port}")\
            .format(self)

    def __hash__(self):
        """
        Return the hash of the Bearer
        """
        return hash(str(self.ue.imsi) + str(self.bid))

    def __eq__(self, other):
        """
        Return True if the Bearer is equal to the object passed as an argument
        """
        other_is_bearer = isinstance(other, self.__class__)
        return other_is_bearer and self.ue.imsi == other.ue.imsi and \
               self.bid == other.bid

    def __lt__(self, other):
        """
        Return True if the Bearer's UE's IMSI is less than to the object
        passed as an argument, or the IMSI is the same but the BID of the
        current Bearer is less than the BID of the argument.
        """
        return self.ue < other.ue or (self.ue.imsi == other.ue.imsi and
                                      self.bid < other.bid)

    def queue_used(self):
        """
        Return the amount of Bytes of the RLC queue currently in use
        """
        amount = 0
        for p in self._queue:
            amount += p.size - p.tx_size
        return amount

    def pending_size(self):
        """
        Return the total size of the queue that still needs to be allocated RBs.
        This does not include the Bytes currently waiting for retransmission.
        """
        amount = 0
        for p in self._queue:
            amount += p.pending_size()
        return amount

    def queue_used_per_packet(self):
        """
        Return a list with the size still in queue of each packet in the queue.
        """
        amounts = []
        for p in self._queue:
            amounts.append(p.size - p.tx_size)
        return amounts

    def add_packet(self, packet):
        """
        Add a packet to the RLC queue. If the packet's size is larger than
        the remaining available space in the queue, the packet is discarded
        and it's size is recorded as a loss.
        """
        amount_used = self.queue_used()
        if amount_used + packet.size <= self.queue_size:
            self._queue.append(packet)
        else:
            time_idx = qppsim.Des.get_des().now().nearest_second()
            if time_idx not in self._loss:
                self._loss[time_idx] = 0
            self._loss[time_idx] += packet.size

    def tx(self, amount, rtx=False):
        """
        Transmit a certain amount of Bytes from the RLC queue. If the 'rtx' flag
        is set to 'True', the Bytes are considered to have been transmitted with
        errors, and therefore they must be set aside awaiting retransmission. If
        the flag is set to 'False', then the Bytes are successfully transmitted.
        In this case we need to record the Bytes as the bearer throughput for
        this unit of time, and also check if a packet is fully transmitted, to
        report it to the application as 'received' after TX_DELAY milliseconds.
        and record the size in the throughput statistic.

        We need to consider that the amount of Bytes to transmit may be larger
        than the pending size of a single packet, and if this happens, we need
        to continue transmitting bytes of the next packet, as needed.
        """
        current_time = qppsim.Des.get_des().now()
        index = 0
        amount_remaining = amount
        while amount_remaining > 0 and index < len(self._queue):
            transmitted = self._queue[index].transmit_bytes(amount_remaining, rtx)
            amount_remaining -= transmitted
            if not rtx:
                time_idx = current_time.nearest_second()
                if time_idx not in self._throughput:
                    self._throughput[time_idx] = 0
                self._throughput[time_idx] += transmitted
                if self._queue[index].tx_size == self._queue[index].size:
                    event = qppsim.Event.Event(
                        current_time + TX_DELAY,
                        self._queue[index].app,
                        self._queue[index].app.receive_packet, [self._queue[index]])
                    qppsim.Des.get_des().add_event(event)
                    del self._queue[index]
                else:
                    index += 1
            else:
                index += 1

    def rtx(self, amount):
        """
        Successfully retransmit a certain amount of Bytes. This method explores
        the queue and marks up to the specified amount of bytes as successfully
        transmitted, and records the throughput for this time period. When this
        operation 'completes' the transmission of a packet we schedule the
        reception by the application after TX_DELAY milliseconds.
        """
        current_time = qppsim.Des.get_des().now()
        index = 0
        amount_remaining = amount
        while amount_remaining > 0 and index < len(self._queue):
            amount_remaining -= self._queue[index].retransmit_bytes(amount_remaining)
            if self._queue[index].tx_size == self._queue[index].size:
                event = qppsim.Event.Event(
                    current_time + TX_DELAY,
                    self._queue[index].app,
                    self._queue[index].app.receive_packet, [self._queue[index]])
                qppsim.Des.get_des().add_event(event)
                del self._queue[index]
            else:
                index += 1
        time_idx = current_time.nearest_second()
        if time_idx not in self._throughput:
            self._throughput[time_idx] = 0
        self._throughput[time_idx] += amount

    def teardown(self):
        """
        Teardown this bearer. This operation shall fail if this is a default bearer.
        Redirect the application linked to this bearer to the UE's default bearer.
        """
        assert self != self.ue.default_bearer, "Cannot tear down the default bearer!"
        self.ue.teardown_bearer(self.bid)
        qppsim.Des.get_des().trace_writer.trace_bearer(
            qppsim.Des.get_des().now(), "DEACTIVATION", self.ue.imsi,
            self.bid, self.qci, self.port)

    def modify_qos(self, new_qci, new_gbr, new_mbr):
        """
        Modify the QoS parameters of the bearer: QCI, GBR, and/or MBR.
        Trace the modification in the bearer trace. Return a boolean indicating
        if the modification succeeded.
        """
        success = qppsim.Des.get_des().access_control_policy.check_bearer_modification(
            self.gbr, self.qci, new_gbr, new_mbr, new_qci,
            self.arp, self.pvi, self.pci, self._ue.imsi, self.bid, self.mcs
            )
        if success:
            qppsim.Des.get_des().trace_writer.trace_bearer_modification(
                qppsim.Des.get_des().now(), self._ue.imsi, self.bid,
                self._qci, new_qci, self.port)
            self.qci = new_qci
            self.gbr = new_gbr
            self.mbr = new_mbr
        return success

    def get_metrics(self):
        """
        Get the QoS metrics stored by this Bearer. Loss and Throughput are
        reported as stored (SortedDicts where the key is the time, and the value
        is the bytes sent / lost), while delays are computed on each call.

        The metrics are returned as a tuple of SortedDicts.
        """
        current_time = qppsim.Des.get_des().now()
        threshold = qppsim.Des.get_des().bearer_stats_window_size
        delays = sortedcontainers.SortedDict()
        for p in self._queue:
            delays[p.tx_time.nearest_second()] = (current_time - p.tx_time)

        min_time = (current_time - threshold).nearest_second()
        if min_time.milliseconds < 0:
            min_time = qppsim.Time.ZERO_TIME

        time_idx = min_time
        while time_idx <= current_time.nearest_second():
            if time_idx not in delays:
                delays[time_idx] = qppsim.Time.Time(float('nan'))
            if time_idx not in self._throughput:
                self._throughput[time_idx] = 0
            if time_idx not in self._loss:
                self._loss[time_idx] = 0
            time_idx += qppsim.Time.ONE_SECOND

        # delete keys smaller than the min_time
        for time_val in self._throughput.irange(maximum=min_time,
                                                inclusive=(True, False)):
            self._throughput.pop(time_val)
            if time_val in self._loss:
                self._loss.pop(time_val)

        return self._throughput, self._loss, delays
