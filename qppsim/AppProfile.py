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
Module that defines an Application Profile.

An Application Profile defines a template for applications that share their
behavior in terms of data rate (defined as the combination of packet size,
inter-packet interval, number of packets per session, and inter-session
interval). These values are defined as tuples containing the name of a
random distribution in numpy.random, and the parameters to such distribution
as a list. Additionally, we can define the distribution to be 'constant',
which will return always the first parameter in the list.
"""

import qppsim.Application
import qppsim.Des
import qppsim.Event
import qppsim.Time


class AppProfile:
    """
    Class that defines an Application Profile.

    An Application Profile defines a template for applications that share their
    behavior in terms of data rate (defined as the combination of packet size,
    inter-packet interval, number of packets per session, and inter-session
    interval). These values are defined as tuples containing the name of a
    random distribution in numpy.random, and the parameters to such distribution
    as a list. Additionally, we can define the distribution to be 'constant',
    which will return always the first parameter in the list.

    The class provides a method to generate an application instance based on
    this profile, by providing the UE where to install the application, and the
    start and stop times.

    The class is hashable and comparable.
    """
    def __init__(self, name, packet_size, packet_interval,
                 packets_session, session_interval):
        """
        Constructor that receives a name (for the string representation), and
        tuples defining the packet size, inter-packet interval, number of
        packets per session, and inter-session interval. Each tuple contains
        the name of a distribution in numpy.random (or "constant"), and a list
        of parameters to the distribution.
        """
        self._name = name
        self._packet_size = packet_size
        self._packet_interval = packet_interval
        self._packets_session = packets_session
        self._session_interval = session_interval

    @property
    def name(self):
        """
        Return the profile name
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

    def __str__(self):
        """
        Return the string representation of this Application Profile
        """
        return ("App Profile: {0.name}" +
                "\n\tPacket Size: {0.packet_size[0]} ({1})" +
                "\n\tPacket Interval: {0.packet_interval[0]} ({2})" +
                "\n\tPackets in Session: {0.packets_session[0]} ({3})" +
                "\n\tSession Interval: {0.session_interval[0]} ({4})").format(
                    self,
                    ", ".join(str(param) for param in self.packet_size[1]),
                    ", ".join(str(param) for param in self.packet_interval[1]),
                    ", ".join(str(param) for param in self.packets_session[1]),
                    ", ".join(str(param) for param in self.session_interval[1])
                    )

    def __hash__(self):
        """
        Return a hash of this application profile
        """
        return hash(str(self.name) +
                    str(self.packet_size) +
                    str(self.packet_interval) +
                    str(self.packets_session) +
                    str(self.session_interval))

    def __eq__(self, other):
        """
        Return True if this object is equal to the parameter passed to the
        method
        """
        return self.name == other.name and \
               self.packet_size == other.packet_size and \
               self.packet_interval == other.packet_interval and \
               self.packets_session == other.packets_session and \
               self.session_interval == other.session_interval

    def create_app(self, name, start_time, stop_time, ue, default_bearer=False):
        """
        Create an application instance based on this profile, with the provided
        start and stop time, and name. The application instance is installed in
        the provided UE
        """
        app = qppsim.Application.Application(name, self.packet_size,
                                             self.packet_interval,
                                             self.packets_session,
                                             self.session_interval,
                                             start_time,
                                             stop_time)
        qppsim.Des.get_des().add_event(
            qppsim.Event.Event(
                start_time - qppsim.Time.Time(milliseconds=100), ue, ue.add_app, [app, default_bearer]))
        return app
