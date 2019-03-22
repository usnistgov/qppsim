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
Module with a Priority Policy that sets a single priority to all applications.
Assigns GBR, MBR, QCI, ARP, PVI, and PCI values.
"""

import qppsim.prioritypolicy.PriorityPolicyBase


class PriorityPolicySample(qppsim.prioritypolicy.PriorityPolicyBase.PriorityPolicyBase):
    """
    Class with a sample Priority Policy that sets a single priority to all applications.
    Assigns GBR, MBR, QCI, ARP, PVI, and PCI values.
    """

    def __init__(self, gbr=1e6, mbr=2e6, qci=2, arp=10, pvi=True, pci=False):
        assert gbr <= mbr, "gbr must be below mbr"

        self.gbr = gbr
        self.mbr = mbr
        self.qci = qci
        self.arp = arp
        self.pvi = pvi
        self.pci = pci

    def get_priority(self, ue, application):
        """
        Get the GBR, MBR, QCI, ARP, PVI, and PCI for a bearer.
        """

        return self.gbr, self.mbr, self.qci, self.arp, self.pvi, self.pci
