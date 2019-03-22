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
Module that provides the model for a Packet.
"""

import qppsim.Des


class Packet:
    """
    Class that models a Packet. A Packet contains the time at which is was
    created, the size (in bytes), the application that created the Packet,
    and a Packet ID (for tracing purposes).

    A packet also keeps track of how many of its bytes have been transmitted,
    and how many are awaiting retransmission.

    The class is hashable and comparable.
    """
    def __init__(self, size, tx_time, app, pid=None):
        """
        Constructor that receives the time at which the packet was created,
        the size in bytes, the application that created the packet, and a PID.

        If the PID is not provided, request one from the DES.
        """
        assert size > 0, "size must be greater than zero"
        if pid is None:
            self._pid = qppsim.Des.get_des().get_packet_id()
        else:
            self._pid = pid
        self._size = size
        self._tx_size = 0
        self._rtx_waiting_size = 0
        self._tx_time = tx_time
        self._app = app
        self._pending = size

    @property
    def pid(self):
        """
        Get the Packet ID.
        """
        return self._pid

    @property
    def size(self):
        """
        Get the Packet size in bytes.
        """
        return self._size

    @property
    def tx_time(self):
        """
        Get the time at which the packet was created.
        """
        return self._tx_time

    @property
    def tx_size(self):
        """
        Get the amount of bytes that have already been transmitted.
        """
        return self._tx_size

    @tx_size.setter
    def tx_size(self, tx_size):
        """
        Set the amount of bytes that have already been transmitted.
        """
        assert tx_size + self.rtx_waiting_size <= self.size, "Attempting to transmit too many bytes! ({0}, {1}, {2})".format(self.size, tx_size, self.rtx_waiting_size)
        self._pending = self._size - tx_size - self._rtx_waiting_size
        self._tx_size = tx_size

    @property
    def rtx_waiting_size(self):
        """
        Get the amount of bytes that are awaiting retransmission.
        """
        return self._rtx_waiting_size

    @rtx_waiting_size.setter
    def rtx_waiting_size(self, rtx_waiting_size):
        """
        Set the amount of bytes that are awaiting retransmission.
        """
        assert rtx_waiting_size + self.tx_size <= self.size, "Attempting to retransmit too many bytes! ({0}, {1}, {2})".format(self.size, self.tx_size, rtx_waiting_size)
        self._pending = self._size - self._tx_size - rtx_waiting_size
        self._rtx_waiting_size = rtx_waiting_size

    @property
    def app(self):
        """
        Get the application that created the Packet.
        """
        return self._app

    def __str__(self):
        """
        Get the string representation of the Packet.
        """
        return "PID: {0.pid}\tSize: {0.size}\tTx Time: {0.tx_time}".format(self)

    def __hash__(self):
        """
        Get a hash of this Packet.
        """
        return hash(str(self.pid) + str(self.size) + str(self.tx_time))

    def __eq__(self, other):
        """
        Check if this Packet is equal to the parameter received.
        """
        return self.pid == other.pid and self.size == other.size and self.tx_time == other.tx_time

    def add_overhead(self, overhead):
        """
        Increase the size of the packet due to lower layers overhead
        """
        self._size += overhead
        return self.size

    def remove_overhead(self, overhead):
        """
        Decrease the size of the packet due to lower layers overhead
        """
        self._size -= overhead
        return self.size

    def pending_size(self):
        """
        Get the amount of bytes that are pending to transmit.
        """
        return self._pending

    def transmit_bytes(self, amount, rtx=False):
        """
        Transmit a certain amount of bytes. If 'rtx' is True, the bytes are
        marked as 'awaiting retransmission'. Otherwise, they are successfully
        transmitted.
        """
        used = 0
        if amount > self.pending_size():
            used = self.pending_size()
        else:
            used = amount

        if rtx:
            self.rtx_waiting_size += used
        else:
            self.tx_size += used

        return used

    def retransmit_bytes(self, amount):
        """
        Successfully transmit a certain amount of bytes from the 'awaiting
        retransmission' bytes.
        """
        used = 0
        if amount > self.rtx_waiting_size:
            used = self.rtx_waiting_size
        else:
            used = amount
        self.rtx_waiting_size -= used
        self.tx_size += used
        return used
