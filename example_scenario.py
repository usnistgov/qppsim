#!/usr/bin/env python3
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
Sample scenario
"""

import qppsim.AppProfile
import qppsim.Des
import qppsim.Time
import qppsim.Ue
import qppsim.accesscontrol.AccessControlSample
import qppsim.preemption.PreemptionDummy
import qppsim.prioritypolicy.PriorityPolicySample
import qppsim.qosmonitor.QosMonitorDefault


if __name__ == "__main__":
    # Step 1: Create the DES engine. In this case, we want access control
    # but not pre-emption, nor QoS monitoring.
    # Also, we don't trace the QoS
    des = qppsim.Des.Des(
        seed=1,
        num_rbs=50,
        stop_time=qppsim.Time.Time(seconds=20),
        rtx_threshold=0.1,
        bearer_stats_window_size=qppsim.Time.Time(seconds=10),
        access_control_policy=qppsim.accesscontrol.AccessControlSample.AccessControlSample(num_rbs=50),
        preemption_policy=qppsim.preemption.PreemptionDummy.PreemptionDummy(),
        priority_policy=qppsim.prioritypolicy.PriorityPolicySample.PriorityPolicySample(),
        qos_monitor=qppsim.qosmonitor.QosMonitorDefault.QosMonitorDefault(),
        trace_qos=True,
        preempt_qos=False
    )

    # Step 2: Create the application profiles. These are templates for the
    # actual instances that will come later.
    cbr_profile = qppsim.AppProfile.AppProfile(
        "CBR_Application_Template",
        ["constant", [750]],       # Packet size
        ["constant", [0.01]],      # Inter-packet interval (in seconds)
        ["constant", [10000000]],  # Packets per session
        ["constant", [0]]          # Inter-session interval (in seconds)
    )

    # Step 3: Create the UEs
    ue01 = qppsim.Ue.Ue(1, "Ue_01", 8, queue_size=10000)
    ue02 = qppsim.Ue.Ue(2, "Ue_02", 8, queue_size=10000)

    # Step 4: Instantiate the applications
    cbr_instance01 = cbr_profile.create_app(
        "CBR_App_01",
        qppsim.Time.Time(seconds=5),
        qppsim.Time.Time(seconds=15),
        ue01
    )
    cbr_instance02 = cbr_profile.create_app(
        "CBR_App_02",
        qppsim.Time.Time(seconds=5),
        qppsim.Time.Time(seconds=15),
        ue01
    )
    cbr_instance03 = cbr_profile.create_app(
        "CBR_App_03",
        qppsim.Time.Time(seconds=5),
        qppsim.Time.Time(seconds=15),
        ue02
    )

    # Step 5: Start the application
    des.start_simulation()
