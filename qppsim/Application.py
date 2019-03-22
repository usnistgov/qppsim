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
Module that provides the implementation of an Application, and an exception to
raise when the Application attempts to send a packet and has no bearer
associated.
"""

import qppsim.Des
import qppsim.Event
import qppsim.Packet

#: Network overhead in bytes to be used when tracing the network-level packet size.
#: This value is taken from the ns-3 simulations, as follows:
#:     - 8 Bytes in UDP header
#:     - 20 Bytes in IPv4 header
#:     - 2 Bytes in PDCP header
NETWORK_OVERHEAD = 30

class NoBearerException(Exception):
    """
    Exception to be raised when an Application attempts to send a packet and
    there is no bearer associated with it.
    """
    pass


class Application:
    """
    Class that defines an Application. An application is defined by the data
    rate (composed of the packet size, inter-packet interval, number of packets
    per session, inter-session interval (all of them defined by tuples with the
    name of a distribution in numpy.random, and a list with parameters to such
    distribution)), the start and stop times, and a name.

    The class also contains a pointer to the Bearer where the packets generated
    are to be queued, and through it, to the UE where the application is
    installed.

    The class provides methods for starting and stopping the packet generation,
    sending and receiving packets, and change the bearer associated with this
    application.
    """
    def __init__(self, name, packet_size, packet_interval,
                 packets_session, session_interval, start_time, stop_time):
        """
        Constructor, receiving the name of the application, and all the
        parameters that define the application data rate. The bearer associated
        with this application is not provided at this time (to avoid a circular
        dependency when creating Bearers), and will be set a later time
        through the setter.

        Note that the start and stop times come from the user-side, so they
        are in seconds, while the simulator works internally in milliseconds,
        so we need to multiply them by 1000
        """
        self._name = name
        self._packet_size = packet_size
        self._packet_interval = packet_interval
        self._packets_session = packets_session
        self._packets_current_session = 0
        self._session_interval = session_interval
        self._start_time = start_time
        self._stop_time = stop_time
        self._count_packets_session = 0
        self._bearer = None
        self._active = False

        assert start_time <= stop_time, ("Start time ({0}) must be smaller " +
                                         "than Stop time ({1})!").format(
                                             start_time, stop_time)
        qppsim.Des.get_des().add_event(
            qppsim.Event.Event(
                self._start_time, self, self.start_app, []))
        qppsim.Des.get_des().add_event(
            qppsim.Event.Event(
                self._stop_time, self, self.stop_app, []))

    @property
    def name(self):
        """
        Return the name of the Application
        """
        return self._name

    @property
    def packet_size(self):
        """
        Return the packet size tuple
        """
        return self._packet_size

    @property
    def packet_interval(self):
        """
        Return the inter-packet interval tuple
        """
        return self._packet_interval

    @property
    def packets_session(self):
        """
        Return the packets per session tuple
        """
        return self._packets_session

    @property
    def session_interval(self):
        """
        Return the inter-session interval tuple
        """
        return self._session_interval

    @property
    def stop_time(self):
        """
        Return the stop time
        """
        return self._stop_time

    @stop_time.setter
    def stop_time(self, stop_time):
        """
        Set the stop time. We need this setter for modifying this value
        dynamically during the simulation
        """
        self._stop_time = stop_time

    @property
    def start_time(self):
        """
        Return the start time
        """
        return self._start_time

    @property
    def bearer(self):
        """
        Return the bearer where this application queues the packets generated
        """
        return self._bearer

    @bearer.setter
    def bearer(self, bearer):
        """
        Set the bearer where this application queues the packets generated
        """
        # This is the initial setting of the bearer, so write it in the
        # topology trace
        if self._bearer is None:
            qppsim.Des.get_des().trace_writer.trace_topology(
                self.name, self.start_time, self.stop_time, bearer.qci,
                bearer.gbr, bearer.mbr, bearer.port)
        self._bearer = bearer

    def __str__(self):
        """
        Return the string representation of this application
        """
        return ("Application: {0.name}" +
                "\n\tPacket Size: {0.packet_size[0]} ({1})" +
                "\n\tPacket Interval: {0.packet_interval[0]} ({2})" +
                "\n\tPackets in Session: {0.packets_session[0]} ({3})" +
                "\n\tSession Interval: {0.session_interval[0]} ({4})" +
                "\n\tStart Time: {5}" +
                "\n\tStop Time: {6}" +
                "\n\tBearer: {0.bearer}").format(
                    self,
                    ", ".join(str(param) for param in self.packet_size[1]),
                    ", ".join(str(param) for param in self.packet_interval[1]),
                    ", ".join(str(param) for param in self.packets_session[1]),
                    ", ".join(str(param) for param in self.session_interval[1]),
                    self.start_time.seconds,
                    self.stop_time.seconds
                    )

    def start_app(self):
        """
        Start generating packets
        """
        self._active = True
        self._packets_current_session = int(
            qppsim.Des.get_des().get_random_value(*self.packets_session))
        self.generate_packet()

    def generate_packet(self):
        """
        Generate a packet, and schedule the event for the next packet generation.
        On the computation of the time for the next event, we need to consider
        if we are the last packet in a session, to adjust the interval until
        the next event.
        """
        if self._active:
            des = qppsim.Des.get_des()
            current_time = des.now()
            if current_time <= self.stop_time:
                try:
                    if self.bearer is None:
                        raise NoBearerException
                    packet = qppsim.Packet.Packet(
                        int(des.get_random_value(*self.packet_size)),
                        current_time, self)
                    des.trace_writer.trace_app_traffic(
                        current_time, self.name, packet.size, packet.pid, "TX")
                    packet.add_overhead (NETWORK_OVERHEAD)
                    self.bearer.add_packet(packet)
                    self._count_packets_session += 1
                    if self._count_packets_session == self._packets_current_session:
                        event = qppsim.Event.Event(
                            current_time +
                            des.get_random_value(*self.session_interval,
                                                 time=True),
                            self, self.generate_packet, [])
                        des.add_event(event)
                        self._count_packets_session = 0
                        self._packets_current_session = int(
                            des.get_random_value(*self.packets_session))
                    else:
                        event = qppsim.Event.Event(
                            current_time +
                            des.get_random_value(*self.packet_interval,
                                                 time=True),
                            self, self.generate_packet, [])
                        des.add_event(event)

                except NoBearerException as err:
                    raise ValueError(err)

    def stop_app(self):
        """
        Stop the application. This method is called when stopping the
        application 'externally'. This also deactivates the associated bearer
        unless it is a default bearer.
        """
        self._active = False
        if self.bearer.bid > 1:
            qppsim.Des.get_des().trace_writer.trace_arp_deactivation(
                qppsim.Des.get_des().now(), self.bearer.ue.imsi, self.bearer.bid,
                self.bearer.qci, self.bearer.gbr, self.bearer.arp,
                self.bearer.pvi, self.bearer.pci)
            self.bearer.teardown()

    def receive_packet(self, packet):
        """
        Receive a packet. The only action performed is removing the network overhead
        and tracing the event in the application traffic trace.
        """
        packet.remove_overhead (NETWORK_OVERHEAD)
        qppsim.Des.get_des().trace_writer.trace_app_traffic(
            qppsim.Des.get_des().now(), self.name, packet.size, packet.pid, "RX")

    def change_bearer(self, new_bearer):
        """
        Change the bearer associated with this application. This may happen
        due to pre-emption, or due to new bearer activation during the
        simulation.
        """
        assert self.bearer.ue.imsi == new_bearer.ue.imsi, (
            "At {0} attempting to change an application bearer to " +
            "a bearer of a different UE! Old IMSI {1} -- New IMSI {2}!!").format(
                qppsim.Des.get_des().now(), self.bearer.ue.imsi, new_bearer.ue.imsi)
        if self.bearer.bid == 1:
            self.bearer.teardown()
        self.bearer = new_bearer
