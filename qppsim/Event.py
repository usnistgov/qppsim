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
Module that provides the model for the simulation events.
"""

import qppsim.Time


class Event:
    """
    Class that models a simulation event. It consists of the time at which the
    event needs to the carried out, the target of the event, the function to
    execute on the target, and the arguments for the function.

    The class is hashable and comparable.
    """
    def __init__(self, time, target, function_, args):
        """
        Constructor, providing the event time, the event target, the function,
        and the arguments for the function.
        """
        self._time = time
        self._target = target
        self._function_ = function_
        self._args = args

    @property
    def time(self):
        """
        Get the event time.
        """
        return self._time

    @property
    def target(self):
        """
        Get the event target.
        """
        return self._target

    @property
    def function_(self):
        """
        Get the event function to execute.
        """
        return self._function_

    @property
    def args(self):
        """
        Get the arguments to the event function.
        """
        return self._args

    def __str__(self):
        """
        Get the string representation of the event.
        """
        target_friendly_name = getattr(self.target, "name", None)
        string = "EVENT: At {0} s: ".format(self.time.seconds)
        if target_friendly_name:
            string += " In {0}: {1.target.__class__.__name__}.{1.function.__name__}({2})".format(target_friendly_name, self, ", ".join(str(a) for a in self.args))
        else:
            string += " {0.target.__class__.__name__}.{0.function.__name__}({1})".format(self, ", ".join(str(a) for a in self.args))
        return string + "\n"

    def __hash__(self):
        """
        Get a hash of the event.
        """
        return hash(str(self.time) + str(self.target) + str(self._function_) + str(self.args))

    def __eq__(self, other):
        """
        Check if this event is equal to the argument provided.
        """
        return self.time == other.time and self.target == other.target and self._function_ == other.function_ and self.args == other.args

    def __lt__(self, other):
        """
        Check if this event's time is lower than that of the argument provided.
        """
        return self.time < other.time
