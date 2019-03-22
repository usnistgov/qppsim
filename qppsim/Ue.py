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
Module with the UE model
"""

import qppsim.BearerList
import qppsim.Des


class Ue:
    """
    Class that models a UE. A UE keeps track of the last BID and port used, and
    provides methods to request the next one available. It also has a fixed MCS
    (configured) at construction time, a dictionary with the applications running
    in the UE, and a reference to the default bearer.

    A UE is defined by its name and IMSI.

    The class is hashable and comparable.
    """
    def __init__(self, imsi, name, mcs, queue_size=10000):
        """
        Constructor. Provides a default value of 10 KB for the RLC queue size if
        no other value is provided.

        The constructor activates the default bearers using the parameters for
        default bearers from the DES
        """
        assert 0 <= mcs <= 28, "MCS ({0}) not between 0 and 28!".format(mcs)

        self._imsi = imsi
        self._name = name
        self._hashval = hash(str(imsi) + str(name))
        self._mcs = mcs
        self._queue_size = queue_size
        self._apps = {}
        self._last_bid = 0
        self._next_port = imsi * 100
        self._bearer_count = 0
        self._default_bearer = qppsim.BearerList.get_bearer_list().add_default_bearer(self, queue_size)

    @property
    def imsi(self):
        """
        Get the IMSI
        """
        return self._imsi

    @property
    def name(self):
        """
        Get the name
        """
        return self._name

    @property
    def mcs(self):
        """
        Get the MCS
        """
        return self._mcs

    @property
    def queue_size(self):
        """
        Get the RLC queue size (in Bytes)
        """
        return self._queue_size

    @property
    def apps(self):
        """
        Get the dictionary with the applications running in this UE
        """
        return self._apps

    @property
    def default_bearer(self):
        """
        Get the default bearer
        """
        return self._default_bearer

    @property
    def bearer_count(self):
        """
        Get the number of active dedicated bearers in this UE
        """
        return self._bearer_count

    @bearer_count.setter
    def bearer_count(self, bearer_count):
        """
        Set the number of active dedicated bearers in this UE
        """
        self._bearer_count = bearer_count

    @property
    def next_port(self):
        """
        Get the next available port
        """
        return self._next_port

    @next_port.setter
    def next_port(self, next_port):
        """
        Set the next available port
        """
        self._next_port = next_port

    def __str__(self):
        """
        Get the string representation of this UE
        """
        print_string = "UE: {0.name}\tIMSI: {0.imsi}\tMCS: {0.mcs}\tQueue Size: {0.queue_size}\n".format(self)

        if self.apps:
            print_string += "\tApplications:\n"
            for key in self.apps:
                print_string += "\t\t" + str(self.apps[key]) + "\n"
        print_string += "\tDefault Bearer:\n"
        print_string += "\t\t" + str(self.default_bearer) + "\n"
        print_string += "\tBearer Count: " + str(self.bearer_count) + "\n"
        print_string += "\tNext Port: " + str(self.next_port) + "\n"

        return print_string

    def __hash__(self):
        """
        Get the hash value of this UE. The value is computed at creation time
        as both the IMSI and the name are immutable.
        """
        return self._hashval

    def __eq__(self, other):
        """
        Check if this UE is equal to the object passed as parameter
        """
        other_is_ue = isinstance(other, self.__class__)
        return other_is_ue and self.imsi == other.imsi

    def __lt__(self, other):
        """
        Check if this UE's IMSI is smaller than the object passed as parameter
        """
        other_is_ue = isinstance(other, self.__class__)
        return other_is_ue and self.imsi < other.imsi

    def add_app(self, app, default_bearer=False):
        """
        Add an application to this UE. If 'default_bearer' is false, we need
        to request the activation of a dedicated bearer for this application,
        using the QoS parameters that the Priority Policy tells us. Otherwise,
        use the default bearer.
        """
        assert self.next_port < ((self.imsi + 1) * 100), (
            "Too many applications configured for IMSI {0}!").format(self.imsi)
        (gbr, mbr, qci, arp, pvi, pci) = qppsim.Des.get_des().priority_policy.get_priority(self, app)
        assert not default_bearer or self.bearer_count < 11, (
            "Cannot add dedicated bearer to UE (IMSI {0.imsi}) with " +
            "{0.__bearer_count} bearers already").format(self)
        if default_bearer:
            b = self.default_bearer
        else:
            b = qppsim.BearerList.get_bearer_list().add_dedicated_bearer(
                self, self.queue_size, qci, gbr, mbr,
                pci, pvi, arp, self.next_port)
            if b is None:
                b = self.default_bearer
            else:
                self.next_port += 1
                self.bearer_count += 1
        app.bearer = b
        self.apps[app.name] = app

    def add_bearer(self, qci, gbr, mbr, pci, pvi, arp):
        """
        Add a dedicated bearer to this UE. Called from the BearerList.
        """
        assert self.next_port < ((self.imsi + 1) * 100), (
            "Too many applications configured for IMSI {0}!").format(self.imsi)
        assert self.bearer_count < 11, (
            "Cannot add dedicated bearer to UE (IMSI {0.imsi}) with " +
            "{0.__bearer_count} bearers already").format(self)
        b = qppsim.BearerList.get_bearer_list().add_dedicated_bearer(
            self, self.queue_size, qci, gbr, mbr,
            pci, pvi, arp, self.next_port)
        if b is not None:
            self.next_port += 1
            self.bearer_count += 1
        return b

    def get_bid(self):
        """
        Get the next available BID
        """
        self._last_bid += 1
        return self._last_bid

    def teardown_bearer(self, bid):
        """
        Deactivate the bearer with the provided ID. Move the application linked
        to that bearer to the default bearer.
        """
        assert bid > 1, "Cannot deactivate bearer with bid {0}!".format(bid)
        for app_name in self.apps:
            if self.apps[app_name].bearer.bid == bid:
                self.apps[app_name].bearer = self.default_bearer
        qppsim.BearerList.get_bearer_list().remove_dedicated_bearer(self, bid)
        self.bearer_count -= 1
