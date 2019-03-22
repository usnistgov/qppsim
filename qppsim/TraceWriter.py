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
Module with the TraceWriter, a class to compile all the tracing operations in
in a single method. It also defines the Network Overhead to be used in the
application traffic traces when reporting the network-level packet size.
"""

import os

import qppsim.qosmonitor.QosMonitorBase

#: Network overhead in bytes to be used when tracing the network-level packet size.
#: This value is taken from the ns-3 simulations, as follows:
#:     - 8 Bytes in UDP header
#:     - 20 Bytes in IPv4 header
#:     - 2 Bytes in PDCP header
NETWORK_OVERHEAD = 30


class TraceWriter:
    """
    Class that provides all the tracing services for the simulation: Application
    Traffic, Bearer, ARP, QoS, and Topology.
    """

    def __init__(self, output_directory, topology_filename,
                 app_traffic_filename, bearer_filename, arp_filename,
                 qos_filename):
        """
        Constructor that gets the filenames for all the trace files, and
        initializes the file handles of the traces to 'None'.

        If any of the filenames is 'None', that means that trace is not to
        be created.
        """
        self._output_directory = output_directory
        self._topology_filename = topology_filename
        self._app_traffic_filename = app_traffic_filename
        self._bearer_filename = bearer_filename
        self._arp_filename = arp_filename
        self._qos_filename = qos_filename

        self._topology_fh = None
        self._app_traffic_fh = None
        self._bearer_fh = None
        self._arp_fh = None
        self._qos_fh = None

    def init_traces(self):
        """
        Initialize the traces, by opening for writing the files (unless the trace
        filename is 'None'), and storing the corresponding file handles.
        """
        if not os.path.exists(self._output_directory):
            raise ValueError("Output directory {0} does not exist (cwd: {1})! ".format(self, os.getcwd()))

        if self._topology_filename:
            self._topology_fh = open(os.path.join(self._output_directory, self._topology_filename), 'w', buffering=1)
        if self._app_traffic_filename:
            self._app_traffic_fh = open(os.path.join(self._output_directory, self._app_traffic_filename), 'w',
                                        buffering=1)
        if self._bearer_filename:
            self._bearer_fh = open(os.path.join(self._output_directory, self._bearer_filename), 'w', buffering=1)
        if self._arp_filename:
            self._arp_fh = open(os.path.join(self._output_directory, self._arp_filename), 'w', buffering=1)
        if self._qos_filename:
            self._qos_fh = open(os.path.join(self._output_directory, self._qos_filename), 'w', buffering=1)

    def close_traces(self):
        """
        Close the open file handles for the traces
        """
        if self._topology_fh:
            self._topology_fh.close()
        if self._app_traffic_fh:
            self._app_traffic_fh.close()
        if self._bearer_fh:
            self._bearer_fh.close()
        if self._arp_fh:
            self._arp_fh.close()
        if self._qos_fh:
            self._qos_fh.close()

    def trace_topology(self, app_name, start_time, stop_time, qci, gbr, mbr, port):
        """
        Trace an entry in the topology trace
        """
        if self._topology_fh:
            self._topology_fh.write(("{0} START_TIME {1:.6f} STOP_TIME {2:.6f} QCI {3} " +
                                     "GBR {4} MBR {5} PORT {6}\n").format
                                    (app_name, start_time.seconds, stop_time.seconds, qci, gbr, mbr, port))

    def trace_app_traffic(self, time, app_name, size, pid, action="TX"):
        """
        Trace an entry in the application traffic trace
        """
        if self._app_traffic_fh:
            self._app_traffic_fh.write("{0} {1:.6f} {2} {3} {4} {5}\n".format
                                       (app_name, time.seconds,
                                        action.upper(), size,
                                        size + NETWORK_OVERHEAD, pid))

    def trace_bearer(self, time, action, imsi, bid, qci, port):
        """
        Trace an entry in the bearer trace
        """
        if self._bearer_fh:
            self._bearer_fh.write(("{0:.6f} {1} IMSI {2} " +
                                   "BID {3} QCI {4} TFT_PORT {5}\n").format
                                  (time.seconds, action.upper(), imsi,
                                   bid, qci, port))

    def trace_bearer_modification(self, time, imsi, bid, old_qci, new_qci, port):
        """
        Trace a modification entry in the bearer trace
        """
        if self._bearer_fh:
            self._bearer_fh.write(("{0:.6f} MODIFICATION IMSI {2} " +
                                   "BID {3} OLD_QCI {4} NEW_QCI {5} TFT_PORT {6}\n").format
                                  (time.seconds, imsi, bid, old_qci,
                                   new_qci, port))

    def trace_arp_activation_check(self, time, imsi, req, used, qci, rate, arp, pvi, pci):
        """
        Trace an ARP Activation Check entry in the ARP trace
        """
        if self._arp_fh:
            self._arp_fh.write(("{0:.6f} ARP_ACTIVATION_CHECK IMSI {1} USED {2} " +
                                "REQ {3} QCI {4} RATE {5} ARP {6} PCI {7} " +
                                "PVI {8}\n").format(
                time.seconds, imsi, used, req,
                qci, rate, arp, pci, pvi))

    def trace_arp_activation_result(self, time, imsi, result, req, used, qci, rate, arp, pvi, pci):
        """
        Trace an ARP Activation Result entry in the ARP trace
        """
        if self._arp_fh:
            self._arp_fh.write(("{0:.6f} ARP_ACTIVATION_RESULT IMSI {1} {2} " +
                                "USED {3} REQ {4} NEW_USED {5} QCI {6} " +
                                "RATE {7} ARP {8} PCI {9} PVI {10}\n").format(
                time.seconds, imsi,
                result.upper(),
                used, req, used + req,
                qci, rate, arp, pci, pvi))

    def trace_arp_modification_check(self, time, imsi, old_req, new_req, used,
                                     old_qci, old_rate, new_qci, new_rate,
                                     arp, pvi, pci):
        """
        Trace an ARP Modification Check entry in the ARP trace
        """
        if self._arp_fh:
            self._arp_fh.write(("{0:.6f} ARP_MODIFICATION_CHECK IMSI {1} USED {2} " +
                                "OLD_REQ {3} NEW_REQ {4} OLD_QCI {5} OLD_RATE {6} " +
                                "NEW_QCI {7} NEW_RATE {8} ARP {9} PCI {10} " +
                                "PVI {11}\n").format(
                time.seconds, imsi, used, old_req, new_req,
                old_qci, new_qci, old_rate, new_rate,
                arp, pci, pvi))

    def trace_arp_modification_result(self, time, imsi, result, old_req, new_req,
                                      used, new_qci, new_rate, arp, pvi, pci):
        """
        Trace an ARP Modification Result entry in the ARP trace
        """
        if self._arp_fh:
            self._arp_fh.write(("{0:.6f} ARP_ACTIVATION_RESULT IMSI {1} {2} " +
                                "USED {3} OLD_REQ {4} NEW_REQ {5} " +
                                "NEW_QCI {6} NEW_RATE {7} " +
                                "ARP {8} PCI {9} PVI {10}\n").format(
                time.seconds, imsi, result.upper(),
                used + new_req, old_req, new_req,
                new_qci, new_rate, arp, pci, pvi))

    def trace_arp_preemption(self, time, imsi, bid, rbs, qci, rate, arp, pvi, pci):
        """
        Trace an ARP Pre-emption entry in the ARP trace
        """
        if self._arp_fh:
            self._arp_fh.write(("{0:.6f} ARP_PRE-EMPTED IMSI {1} BID {2} USED {3} " +
                                "QCI {4} RATE {5} ARP {6} PCI {7} PVI {8}\n"
                                ).format(time.seconds, imsi,
                                         bid, rbs, qci, rate, arp, pci, pvi))

    def trace_arp_deactivation(self, time, imsi, bid, qci, rate, arp, pvi, pci):
        """
        Trace an ARP Deactivation entry in the ARP trace
        """
        if self._arp_fh:
            self._arp_fh.write(("{0:.6f} DEACTIVATION IMSI {1} " +
                                "BID {2} QCI {3} RATE {4} ARP {5} " +
                                "PCI {6} PVI {7}\n"
                                ).format(time.seconds, imsi,
                                         bid, qci, rate, arp, pci, pvi))

    def trace_qos(self, time, imsi, bid, qci, gbr, rate, loss, losspct, delay):
        """
        Trace an entry in the QoS trace
        """
        if self._qos_fh:
            self._qos_fh.write(
                ("{0:.6f} IMSI {1} BID {2} QCI {3} Priority {4} " +
                 "Throughput ({5.minimum} {5.average} {5.maximum} {5.last} -- {6}) " +
                 "Loss ({7.minimum} {7.average} {7.maximum} {7.last} -- {8}) " +
                 "Loss% ({9.minimum} {9.average} {9.maximum} {9.last} -- {10}) " +
                 "Delay ({11.minimum.seconds} {11.average.seconds} {11.maximum.seconds} {11.last.seconds} -- {12})\n"
                 ).format(time.seconds, imsi, bid,
                          qci, qppsim.qosmonitor.QosMonitorBase.QOS_LIMITS_PER_QCI[qci][1],
                          rate, gbr,
                          loss, qppsim.qosmonitor.QosMonitorBase.QOS_LIMITS_PER_QCI[qci][3],
                          losspct, qppsim.qosmonitor.QosMonitorBase.QOS_LIMITS_PER_QCI[qci][3],
                          delay, qppsim.qosmonitor.QosMonitorBase.QOS_LIMITS_PER_QCI[qci][2] / 1000))

