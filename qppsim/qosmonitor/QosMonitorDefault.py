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
Module with the default QoS Monitor. This monitor only uses the values collected
for the last second.
"""

import math

import sortedcontainers

import qppsim.BearerList
import qppsim.Des
import qppsim.qosmonitor.QosMonitorBase
import qppsim.Time


class QosMonitorDefault(qppsim.qosmonitor.QosMonitorBase.QosMonitorBase):
    """
    Default QoS Monitor. This monitor only uses the values collected for the
    last second. The throughput and loss are the total throughput and loss for
    that last second, while the delay is the maximum delay for that second.
    """
    def get_qos(self):
        """
        Get the QoS values for the last second from the active bearers. The
        throughput and loss are the total throughput and loss for that last
        second, while the delay is the maximum delay for that second.

        QosTracing objects are created, and if configured, they are written
        to the QoS trace.

        If configured to do so, check if the QoS of the bearers is missing their
        targets, and if True, pre-empt a bearer.
        """
        current_time = qppsim.Des.get_des().now()
        qos_stats = {}
        qos_stats_trace = {}
        preempted = False
        bearer_list = qppsim.BearerList.get_bearer_list().bearers
        for ue in bearer_list:
            if ue not in qos_stats:
                qos_stats[ue] = {}
                qos_stats_trace[ue] = {}
            for bid in bearer_list[ue]:
                bearer = bearer_list[ue][bid]
                (bearer_throughput, bearer_loss, bearer_delays) = bearer.get_metrics()
                throughput = sum(v for (k, v) in bearer_throughput.items() if current_time - k < qppsim.Time.ONE_SECOND)
                # For tracing
                trace_throughput = qppsim.qosmonitor.QosMonitorBase.TraceableQos(
                    min(v for (k, v) in bearer_throughput.items() if current_time - k < qppsim.Time.ONE_SECOND),
                    sum(v for (k, v) in bearer_throughput.items() if current_time - k < qppsim.Time.ONE_SECOND) / sum(1 for i in (v for (k, v) in bearer_throughput.items() if current_time - k < qppsim.Time.ONE_SECOND)),
                    max(v for (k, v) in bearer_throughput.items() if current_time - k < qppsim.Time.ONE_SECOND),
                    bearer_throughput.peekitem(-1)[1]
                    )

                current_second_losses = list({key: value for key, value in bearer_loss.items() if current_time - key < qppsim.Time.ONE_SECOND}.values())
                # Special case average as 0 when no applicable items are found
                if current_second_losses:
                    loss_average = sum(current_second_losses)/len(current_second_losses)
                else:
                    loss_average = 0

                loss = sum(v for (k, v) in bearer_loss.items() if current_time - k < qppsim.Time.ONE_SECOND)
                if loss > 0 or throughput > 0:
                    losspct = loss / (loss + throughput)
                else:
                    losspct = 0
                trace_loss = qppsim.qosmonitor.QosMonitorBase.TraceableQos(
                    min(current_second_losses),
                    loss_average,
                    max(current_second_losses),
                    bearer_loss.peekitem(-1)[1]
                    )

                losspct_values = sortedcontainers.SortedDict()
                for time_val in bearer_loss.irange(minimum=current_time - qppsim.Time.ONE_SECOND,
                                                   inclusive=(False, True)):
                    if bearer_loss[time_val] > 0 or bearer_throughput[time_val] > 0:
                        losspct_values[time_val] = bearer_loss[time_val] / (bearer_loss[time_val] + bearer_throughput[time_val])
                    else:
                        losspct_values[time_val] = 0
                trace_losspct = qppsim.qosmonitor.QosMonitorBase.TraceableQos(
                    min(losspct_values.values()),
                    sum(losspct_values.values()) / len(losspct_values),
                    max(losspct_values.values()),
                    losspct_values.values()[-1]
                    )

                current_second_delays = list({key: value for key, value in bearer_delays.items() if current_time - key < qppsim.Time.ONE_SECOND}.values())
                # Special case average as 0 when no applicable items are found
                if current_second_delays:
                    trace_delay_average = qppsim.Time.Time(milliseconds=sum(current_second_delays, qppsim.Time.ZERO_TIME).milliseconds/len(current_second_delays))
                else:
                    trace_delay_average = qppsim.Time.ZERO_TIME
                # For tracing
                trace_delay = qppsim.qosmonitor.QosMonitorBase.TraceableQos(
                    min(current_second_delays),
                    trace_delay_average,
                    max(current_second_delays),
                    bearer_delays.peekitem(-1)[1]
                    )

                delay = max(v for (k, v) in bearer_delays.items() if current_time - k < qppsim.Time.ONE_SECOND)
                qos_stats[ue][bid] = (throughput, loss, losspct, delay)
                qos_stats_trace[ue][bid] = (bearer.qci, bearer.gbr,
                                            trace_throughput,
                                            trace_loss,
                                            trace_losspct,
                                            trace_delay)

                if self.preempt_qos and not preempted and (
                        losspct > qppsim.qosmonitor.QosMonitorBase.QOS_LIMITS_PER_QCI[bearer.qci][3]
                        or (not math.isnan(delay.milliseconds) and
                            delay.milliseconds > qppsim.qosmonitor.QosMonitorBase.QOS_LIMITS_PER_QCI[bearer.qci][2]
                           )
                    ):
                    #Pre-empt due to loss or delays of a bearer
                    #Pre-empt only once per call to the function
                    (success, bearers_to_preempt) = qppsim.Des.get_des().preemption_policy.qos_preemption(ue.imsi, bid, bearer.arp)
                    if success:
                        #Pre-empt only once per TTI
                        preempted = True
                        bearer = bearers_to_preempt[0]
                        qppsim.Des.get_des().trace_writer.trace_arp_deactivation(
                            qppsim.Des.get_des().now(), bearer.ue.imsi, bearer.bid,
                            bearer.qci, bearer.gbr, bearer.arp, bearer.pvi,
                            bearer.pci)
                        bearer.teardown()

        self.do_trace_qos_stats(qos_stats_trace)
        return qos_stats
