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
Module with the base class for QoS Monitors and a class to store the QoS values
so they can be easily traced by the TraceWriter. It also provides a constant
dictionary with the QoS parameters associated with each QCI value.
"""

from abc import ABCMeta, abstractmethod

import qppsim.Des

#: Dictionary with the QoS limits and parameters associated with each QCI value
#: Key: QCI
#: Value: Tuple with GBR/NGBR flag, Priority, Maximum Delay, Error and Loss Rate
QOS_LIMITS_PER_QCI = {1: (True, 2, 100, 1e-2),
                      2: (True, 4, 150, 1e-3),
                      3: (True, 3, 50, 1e-3),
                      4: (True, 5, 300, 1e-6),
                      5: (False, 1, 100, 1e-6),
                      6: (False, 6, 300, 1e-6),
                      7: (False, 7, 100, 1e-3),
                      8: (False, 8, 300, 1e-6),
                      9: (False, 9, 300, 1e-6),
                     }


class QosMonitorBase(metaclass=ABCMeta):
    """
    Base class for QoS Monitors. Defines a method for getting and aggregating
    the QoS metrics from the active bearers. Implements a method to trace the
    collected QoS metrics.
    """
    def __init__(self):
        """
        Constructor. By default, do not pre-empt based on QoS, and do not trace
        the QoS. These attributes are public, so can be modified by the DES
        according to its parameters.
        """
        self.preempt_qos = False
        self.trace_qos = False

    @abstractmethod
    def get_qos(self):
        """
        Method for getting and aggregating the QoS metrics from the active bearer.
        Not implemented.
        """
        pass

    def do_trace_qos_stats(self, qos_stats):
        """
        Method to trace the collected QoS metrics.
        """
        if self.trace_qos:
            for ue in qos_stats:
                for bid in qos_stats[ue]:
                    qppsim.Des.get_des().trace_writer.trace_qos(
                        qppsim.Des.get_des().now(), ue.imsi, bid,
                        *(qos_stats[ue][bid]))


class TraceableQos:
    """
    Class that provides a format to trace QoS values, composed by the minimum,
    average, maximum, and last values obtained.
    """
    def __init__(self, minimum, average, maximum, last):
        """
        Constructor.
        """
        self.__minimum = minimum
        self.__average = average
        self.__maximum = maximum
        self.__last = last

    @property
    def minimum(self):
        """
        Get the minimum value of the QoS values.
        """
        return self.__minimum

    @property
    def average(self):
        """
        Get the average value of the QoS values.
        """
        return self.__average

    @property
    def maximum(self):
        """
        Get the maximum value of the QoS values.
        """
        return self.__maximum

    @property
    def last(self):
        """
        Get the last value of the QoS values.
        """
        return self.__last
