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
Module that provides the model for the List of all bearers in the simulation.
The class is static, and the module function 'get_bearer_list' provides access
to the instance.
"""

import sortedcontainers

import qppsim.Bearer
import qppsim.Des

#: Reference to the active instance of this class
instance = None


def get_bearer_list():
    """
    Get a reference to the instance of the BearerList class. If there is none,
    a new instance is created.
    """
    global instance
    if instance is None:
        instance = BearerList()
    return instance


class BearerList:
    """
    Class that represents the list with all the bearers active in the simulation.
    Bearers are created in this class, and returned to the requester of the
    bearer.

    Methods are provided for adding a default bearer, adding a dedicated bearer,
    and deactivating an active bearer.
    """
    def __init__(self):
        """
        Constructor. Point the global reference to this object, and initialize
        the list of bearers as an empty SortedDict.
        """
        global instance
        if instance:
            del instance
        instance = self
        self.bearers = sortedcontainers.SortedDict()

    def __str__(self):
        """
        Return the string representation of this bearer list.
        """
        string = "BEARER LIST"

        for ue in self.bearers:
            string += "\n\tUE {0.name} (IMSI {0.imsi})".format(ue)
            for bearer in self.bearers[ue]:
                string += "\n\t\t{0})".format(bearer)
        return string

    def add_default_bearer(self, ue, queue_size):
        """
        Create a default bearer for the UE, with the QoS parameters set as
        default for the Simulation (in the Des), and the RLC queue size
        specified. Add the bearer to the bearer list.
        """
        des = qppsim.Des.get_des()
        bearer_ok = des.access_control_policy.check_bearer_activation(
            0, des.default_mbr, des.default_qci, des.default_arp,
            False, False, ue.imsi, 1, ue.mcs)
        if bearer_ok:
            bearer = qppsim.Bearer.Bearer(ue, des.default_qci, 0,
                                          des.default_mbr, False, False,
                                          des.default_arp, queue_size, None)
        else:
            raise RuntimeError("Default Bearer should not fail to be added")

        self.bearers[ue] = sortedcontainers.SortedDict()
        self.bearers[ue][bearer.bid] = bearer
        return bearer

    def add_dedicated_bearer(self, ue, queue_size, qci,
                             gbr, mbr, pci, pvi, arp, port):
        """
        Create a dedicated bearer for the UE, with the QoS parameters received
        in the call, and the RLC queue size specified. Add the bearer to the
        bearer list.
        """
        assert ue in self.bearers, "No default bearer for UE {0.name},{0.imsi}!".format(ue)

        dedicated_bearer = qppsim.Des.get_des().access_control_policy.check_bearer_activation(
            gbr, mbr, qci, arp, pvi, pci, ue.imsi, ue.get_bid(), ue.mcs)
        if dedicated_bearer:
            bearer = qppsim.Bearer.Bearer(ue, qci, gbr, mbr, pvi, pci, arp, queue_size, port)
            self.bearers[ue][bearer.bid] = bearer
        else:
            bearer = None

        return bearer

    def remove_dedicated_bearer(self, ue, bid):
        """
        Remove a dedicated bearer from the list.
        """
        assert bid > 1, "Cannot deactivate bearer with bid {0}!".format(bid)
        assert ue in self.bearers, "UE (IMSI {0.imsi}) not in list of bearers!".format(ue)
        assert bid in self.bearers[ue], "BID {0} not in list for IMSI {1.imsi}!".format(bid, ue)

        del self.bearers[ue][bid]
