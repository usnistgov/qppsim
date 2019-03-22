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
Module with the DES code. The Des class is static, and the 'get_des' method
provides access to the active instance.
"""

import os
import sys

import numpy
import sortedcontainers

import qppsim.BearerList
import qppsim.Event
import qppsim.Time
import qppsim.TraceWriter

import qppsim.accesscontrol.AccessControlTraceOnly
import qppsim.preemption.PreemptionDummy
import qppsim.qosmonitor.QosMonitorDummy
import qppsim.scheduler.SchedulerRoundRobin


#: Reference to the active instance of this class
instance = None


def get_des(new_instance=False):
    """
    Get a reference to the instance of the Des class. If there is none,
    a new instance is created with the default parameters.
    """
    global instance
    if instance is None or new_instance:
        instance = Des()
    return instance


class Des:
    """
    Class that represents the Discrete Event Simulation engine. It stores
    the default configuration for default bearers, trace filenames, seed,
    global packet ID counter, current simulation time, Priority, Access Control,
    Pre-emption, Scheduler and QoS Monitor policies, TX error probability,
    and the reference to the TraceWriter.

    Methods are provided for getting random values from random distributions,
    computing if a transmission succeeded, get the current simulation time,
    start and stop the simulation, add events to the DES, and activate and
    deactivate bearers and specific times.
    """
    def __init__(self, num_rbs=50, start_packet_id=0, default_qci=9,
                 default_arp=11, default_mbr=1024*1024*1024*1024,
                 rtx_threshold=0.1,
                 bearer_stats_window_size=qppsim.Time.Time(seconds=60),
                 seed=1, stop_time=qppsim.Time.Time(seconds=1),
                 priority_policy=None,
                 access_control_policy=None,
                 preemption_policy=None,
                 qos_monitor=None,
                 scheduler=None,
                 output_dir=".",
                 topology_filename="topologyTrace.txt",
                 app_traffic_filename="trafficTrace.txt",
                 bearer_filename="bearerTrace.txt",
                 arp_filename="arpTrace.txt",
                 qos_filename="qosTrace.txt",
                 trace_qos=False,
                 preempt_qos=False,
                 qos_monitor_interval=qppsim.Time.Time(seconds=1)):
        """
        Constructor. Provides default values for the filenames for traces,
        QoS parameters for default bearers, TX error probability, seed,
        Priority, Access Control, Pre-emption, QoS Monitor and Scheduler policies,
        QoS Monitor interval, ending simulation time, and total number of RBs.

        Point the global reference to the active instance. dynamically load the
        policies modules (may be outside this package), create the TraceWriter
        instance and initialize the trace files, and reset the event list,
        packet ID counter, and current simulation time.
        """
        global instance
        if instance:
            del instance
        instance = self

        self._num_rbs = num_rbs
        self._packet_id = start_packet_id
        self._default_qci = default_qci
        self._default_arp = default_arp
        self._default_mbr = default_mbr
        self._rtx_threshold = rtx_threshold
        self._bearer_stats_window_size = bearer_stats_window_size
        self._seed = seed
        numpy.random.seed(seed)
        self._stop_time = stop_time

        if priority_policy is None:
            raise ValueError("priority_policy Must Be Defined Manually")
        self._priority_policy = priority_policy

        if access_control_policy is None:
            self._access_control_policy = qppsim.accesscontrol.AccessControlTraceOnly.AccessControlTraceOnly(num_rbs=num_rbs)
        else:
            self._access_control_policy = access_control_policy

        if preemption_policy is None:
            self._preemption_policy = qppsim.preemption.PreemptionDummy.PreemptionDummy()
        else:
            self._preemption_policy = preemption_policy

        if qos_monitor is None:
            self._qos_monitor = qppsim.qosmonitor.QosMonitorDummy.QosMonitorDummy()
        else:
            self._qos_monitor = qos_monitor

        self._qos_monitor.trace_qos = trace_qos
        self._qos_monitor.preempt_qos = preempt_qos
        self._qos_monitor_interval = qos_monitor_interval

        if scheduler is None:
            self._scheduler = qppsim.scheduler.SchedulerRoundRobin.SchedulerRoundRobin(num_rbs=num_rbs)
        else:
            self._scheduler = scheduler

        self._output_dir = output_dir
        self._topology_filename = topology_filename
        self._app_traffic_filename = app_traffic_filename
        self._bearer_filename = bearer_filename
        self._arp_filename = arp_filename
        self._qos_filename = qos_filename
        self._trace_writer = qppsim.TraceWriter.TraceWriter(
            self.output_dir, self.topology_filename, self.app_traffic_filename,
            self.bearer_filename, self.arp_filename, self.qos_filename)
        self._trace_writer.init_traces()

        self._events = sortedcontainers.SortedList()
        self._current_time = qppsim.Time.ZERO_TIME

    @property
    def num_rbs(self):
        """
        Return the total number of RBs to allocate in each TTI.
        """
        return self._num_rbs

    @property
    def default_qci(self):
        """
        Return the QCI for default bearers.
        """
        return self._default_qci

    @property
    def default_arp(self):
        """
        Return the ARP for default bearers.
        """
        return self._default_arp

    @property
    def default_mbr(self):
        """
        Return the MBR for default bearers.
        """
        return self._default_mbr

    @property
    def rtx_threshold(self):
        """
        Return probability of TX error.
        """
        return self._rtx_threshold

    @property
    def bearer_stats_window_size(self):
        """
        Return the length of time for which the bearers will store QoS metrics.
        """
        return self._bearer_stats_window_size

    @property
    def seed(self):
        """
        Return the random seed used in the simulation.
        """
        return self._seed

    @property
    def stop_time(self):
        """
        Return the simulation stop time.
        """
        return self._stop_time

    @property
    def priority_policy(self):
        """
        Return the reference to the active Priority policy.
        """
        return self._priority_policy

    @property
    def access_control_policy(self):
        """
        Return the reference to the active Access Control module.
        """
        return self._access_control_policy

    @property
    def preemption_policy(self):
        """
        Return the reference to the active Pre-emption module.
        """
        return self._preemption_policy

    @property
    def qos_monitor(self):
        """
        Return the reference to the active QoS Monitor.
        """
        return self._qos_monitor

    @property
    def scheduler(self):
        """
        Return the reference to the active Scheduler.
        """
        return self._scheduler

    @property
    def output_dir(self):
        """
        Return the output directory for the traces.
        """
        return self._output_dir

    @property
    def topology_filename(self):
        """
        Return the topology trace filename
        """
        return self._topology_filename

    @property
    def app_traffic_filename(self):
        """
        Return the filename for the application traffic trace.
        """
        return self._app_traffic_filename

    @property
    def bearer_filename(self):
        """
        Return the filename for the bearer trace.
        """
        return self._bearer_filename

    @property
    def arp_filename(self):
        """
        Return the filename for the ARP trace.
        """
        return self._arp_filename

    @property
    def qos_filename(self):
        """
        Return the filename for the QoS trace.
        """
        return self._qos_filename

    @property
    def trace_writer(self):
        """
        Return a reference to the active TraceWriter.
        """
        return self._trace_writer

    @property
    def qos_monitor_interval(self):
        """
        Return the interval at which the scheduler checks the bearers QoS.
        """
        return self._qos_monitor_interval

    @qos_monitor_interval.setter
    def qos_monitor_interval(self, qos_monitor_interval):
        """
        Set the interval at which the scheduler checks the bearers QoS.
        """
        self._qos_monitor_interval = qos_monitor_interval

    @property
    def packet_id(self):
        """
        Get the last packet ID assigned
        """
        return self._packet_id

    def __str__(self):
        """
        Return the string representation of the DES.
        """
        string = ("""DES:
\t{0.num_rbs} RBs
\tNext Packet ID: {0.packet_id}
\tDefault bearer config: QCI {0.default_qci} ARP {0.default_arp} MBR {0.default_mbr}
\tRTX Threshold: {0.rtx_threshold}
\tBearer Stats Window Size: {0.bearer_stats_window_size}
\tSeed: {0.seed}
\tStop Time: {1}
\tPolicies:
\t\tApplication Priority Policy: {0.priority_policy}
\t\tAccess Control Policy: {0.access_control_policy}
\t\tPre-emption Policy: {0.preemption_policy}
\t\tQoS Monitor Policy: {0.qos_monitor}
\tScheduler: {0.scheduler}
\tOutput Directory: {2}
\t\tTopology Trace File Name: {0.topology_filename}
\t\tApplication Traffic Trace File Name: {0.app_traffic_filename}
\t\tBearer Trace File Name: {0.bearer_filename}
\t\tAccess Control Trace File Name: {0.arp_filename}
\t\tQoS Trace File Name: {0.qos_filename}
\tCurrent Time: {3}
\tEVENTS:
""").format(self, self.stop_time.milliseconds,
            os.path.realpath(self.output_dir), self.now())

        for event in self._events:
            string += "\t\t{0}".format(event)

        return string

    def get_random_value(self, distribution_name, args, time=False):
        """
        Get a random value from the specified random distribution, with the
        provided parameters. If 'time' is True, the requested random value is
        supposed to be a time, so we need to multiply it by 1000 to convert it
        to milliseconds (as the user specifies the random parameters for
        timings in seconds, for convenience).

        :return a random value from the passed numpy.random function, as A Time object if time is True

        :rtype float, qppsim.Time.Time

        :raise AttributeError
        The random distribution specified by distribution_name was not found
        in numpy.random
        """
        if distribution_name == "constant":
            value = args[0]
        else:
            try:
                random_function = getattr(numpy.random, distribution_name)
            except AttributeError:
                print("Random Distribution '{0}' not found".format(distribution_name),
                      file=sys.stderr)
                raise
            else:
                value = random_function(*args)
        if time:
            return qppsim.Time.Time(seconds=value)
        return value

    def get_tx_success(self):
        """
        Check if a transmission is successful or not. It uses a uniform random
        distribution and the TX error probability.
        """
        value = numpy.random.uniform()
        return value >= self.rtx_threshold

    def get_packet_id(self):
        """
        Get the next available Packet ID, and increase the counter.
        """
        self._packet_id += 1
        return self._packet_id

    def now(self):
        """
        Get the current simulation time.
        """
        return self._current_time

    def add_event(self, event):
        """
        Add an event to the DES event queue.
        """
        assert event.time >= self.now(),\
            ("Attempting to schedule an event in the past!" +
             "\n\tCurrent time: {0}\n\tEvent time: {1}").format(
                 self._current_time.milliseconds, event.time.milliseconds
                 )
        self._events.add(event)

    def end_simulation(self):
        """
        End the simulation, and close the trace filenames.
        """
        self._trace_writer.close_traces()

    def start_simulation(self):
        """
        Start the simulation. Create the events to stop the simulation and the
        scheduling for the first TTI, and then process the event queue until we
        hit the 'end_simulation' event.
        """
        self.add_event(qppsim.Event.Event(self.stop_time, self, self.end_simulation, []))
        self.add_event(qppsim.Event.Event(qppsim.Time.Time(seconds=0), self.scheduler, self.scheduler.schedule, []))

        while self._events:
            event = self._events.pop(0)
            assert event.time >= self._current_time, "Attempting to run an event in the past!"
            self._current_time = event.time
            if event.function_ == self.end_simulation:
                self._events.clear()
                self.end_simulation()
            else:
                event.function_(*event.args)

    def deactivate_bearer_at_time(self, time, ue, bid):
        """
        Add an event to deactivate a bearer at a given time.
        """
        self.add_event(qppsim.Event.Event(time, self, self.do_deactivate_bearer, [ue, bid]))

    def do_deactivate_bearer(self, ue, bid):
        """
        Deactivate a bearer.
        """
        # Find the bearer
        try:
            bearer = qppsim.BearerList.get_bearer_list().bearers[ue][bid]
            self.trace_writer.trace_arp_deactivation(
                self._current_time, bearer.ue.imsi, bearer.bid, bearer.qci,
                bearer.gbr, bearer.arp, bearer.pvi, bearer.pci)
            bearer.teardown()
        except KeyError as err:
            print("At {0} Attempting to deactivate bearer that does not exist! IMSI {1} BID {2}!!".format(self.now(), ue.imsi, bid))
            raise err

    def activate_bearer_at_time(self, time, app, qci, gbr, mbr, pci, pvi, arp):
        """
        Add an event to activate a bearer for a given application at a given time.
        """
        self.add_event(qppsim.Event.Event(time, self, self.do_activate_bearer,
                                          [app, qci, gbr, mbr, pci, pvi, arp]))

    def do_activate_bearer(self, app, qci, gbr, mbr, pci, pvi, arp):
        """
        Activate a bearer for a given application at a given time.
        """
        new_bearer = app.bearer.ue.add_bearer(qci, gbr, mbr, pci, pvi, arp)
        if new_bearer.bid > 1:
            app.change_bearer(new_bearer)
        else:
            new_bearer = None
        return new_bearer
