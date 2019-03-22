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
Base class for the Access Control models
"""

from abc import ABCMeta, abstractmethod

import qppsim.Amc
import qppsim.BearerList
import qppsim.Des


class AccessControlBase(metaclass=ABCMeta):
    """
    Base class for the Access Control Models. It provides a method to compute the
    RBs currently reserved for GBR bearers, a method to compute the RBs needed to
    to provide a give GBR rate on a given MCS, and a method to trace a bearer
    deactivation.

    It also defines the method to be called when creating a new bearer, that checks
    whether a bearer can be accepted into the network. The implementation of this
    method is left to the child classes, and it shall return a boolean.
    """
    def __init__(self, num_rbs):
        """
        Constructor that initializes the number of RBs available in each TTI
        """
        self.__num_rbs = num_rbs

    @property
    def num_rbs(self):
        """
        Return the total number of RBs available in each TTI.
        """
        return self.__num_rbs

    def get_used_gbr_rbs(self):
        """
        Return an integer with the number of RBs currently reserved for GBR bearers.
        """
        used = 0
        bearer_list = qppsim.BearerList.get_bearer_list().bearers
        for ue in bearer_list:
            for bid in bearer_list[ue]:
                bearer = bearer_list[ue][bid]
                if bearer.qci < 5:
                    (found, count) = qppsim.Amc.get_rbs_for_rate(bearer.ue.mcs,
                                                                 bearer.gbr)
                    if found:
                        used += count
        return used

    def get_needed_gbr_rbs(self, gbr, mcs, qci):
        """
        Return an integer with the number of RBs needed in a second to provide the GBR rate
        at the provided MCS.
        """
        needed = 0
        if qci < 5:
            (found, count) = qppsim.Amc.get_rbs_for_rate(mcs, gbr)
            if found:
                needed = count
            else:
                # If we cannot find the entry in the table, return a value that is larger 
                # than the available space
                needed = self.__num_rbs * 1000 + 1
        return needed

    @abstractmethod
    def check_bearer_activation(self, gbr, mbr, qci, arp, pvi, pci,
                                imsi, bid, mcs):
        """
        Return a boolean stating if a bearer with the given GBR, MBR, QCI, ARP,
        PVI, PCI, and MCS for the UE with the given IMSI can be activated.

        To be implemented by subclasses.
        """
        pass

    @abstractmethod
    def check_bearer_modification(self, old_gbr, old_qci,
                                  new_gbr, new_mbr, new_qci,
                                  arp, pvi, pci, imsi, bid, mcs):
        """
        Return a boolean stating if a bearer can be modified from the old GBR
        and QCI to the new provided GBR, MBR, QCI, ARP, PVI, PCI, and MCS.

        To be implemented by subclasses.
        """
        pass

    def bearer_deactivation(self, bearer):
        """
        Trace a bearer deactivation in the ARP trace
        """
        qppsim.Des.get_des().trace_writer.trace_arp_deactivation(
            qppsim.Des.get_des().now(), bearer.ue.imsi, bearer.bid,
            bearer.qci, bearer.gbr, bearer.arp, bearer.pvi, bearer.pci)
