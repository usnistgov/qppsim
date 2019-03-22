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
Module to allow for universal time representation
independent of the unit.
"""


class Time:
    """
    Immutable Representation of Time in the simulation.
    With the smallest difference between two Times being one milliseconds.

    The class is hashable and comparable.
    """

    def __init__(self, milliseconds=0, seconds=0):
        """
        Initialize a Time object with a predefined time
        """
        self.milliseconds = milliseconds + seconds * 1000

    def __eq__(self, other):
        """
        Tests if two Time objects are equal
        Comparisons with other types are not implemented
        """
        if not isinstance(other, Time):
            return NotImplemented
        return self.milliseconds == other.milliseconds

    def __lt__(self, other):
        """
        Tests if this Time object is less than another
        Comparisons with other types are not implemented
        """
        if not isinstance(other, Time):
            return NotImplemented
        return self.milliseconds < other.milliseconds

    def __le__(self, other):
        """
        Tests if this Time object is less than or equal to another
        Comparisons with other types are not implemented
        """
        if not isinstance(other, Time):
            return NotImplemented
        return self.milliseconds <= other.milliseconds

    def __gt__(self, other):
        """
        Tests if this Time object is greater than another
        Comparisons with other types are not implemented
        """
        if not isinstance(other, Time):
            return NotImplemented
        return self.milliseconds > other.milliseconds

    def __ge__(self, other):
        """
        Tests if this Time object is greater than or equal to another
        Comparisons with other types are not implemented
        """
        if not isinstance(other, Time):
            return NotImplemented
        return self.milliseconds >= other.milliseconds

    def __hash__(self):
        """
        Generate a hash based on stored Time
        """
        # hash Protects us when milliseconds is not an int
        return hash(self.milliseconds)

    def __str__(self):
        """
        Give a simple representation of this object
        """
        return "Time(milliseconds:{0})".format(self.milliseconds)

    def __add__(self, other):
        if not isinstance(other, Time):
            return NotImplemented
        return Time(milliseconds=self.milliseconds + other.milliseconds)

    def __sub__(self, other):
        if not isinstance(other, Time):
            return NotImplemented
        return Time(milliseconds=self.milliseconds - other.milliseconds)

    def nearest_second(self):
        """
        Return the nearest rounded second to the current value
        """
        return Time(milliseconds=round(self.milliseconds, -3))

    @property
    def seconds(self):
        """
        Returns the stored time as seconds
        """
        return self.milliseconds / 1000


ZERO_TIME = Time()
"""
Convenience constant zero milliseconds (no time)
"""


ONE_MILLISECOND = Time(milliseconds=1)
"""
Convenience constant for one millisecond
"""


ONE_SECOND = Time(seconds=1)
"""
Convenience constant for one second
"""
