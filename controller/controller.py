#! /usr/bin/env python3

import os
import re
import time
import json
import logging
import pickle
import threading
import requests
from argparse import ArgumentParser
from configparser import ConfigParser
from pathlib import Path
from tempfile import NamedTemporaryFile
from cs import read_config, CloudStack

import catalog

#
CONFIG_FILE = "/auto-scaling/cloudstack.ini"
STATUS_FILE = "/auto-scaling/autoscaling.status"
INTERVAL    = 15  #  15 sec
PERIOD      = 180 # 180 sec
USAGE_COUNT = PERIOD / INTERVAL
VM_PREFIX   = "asvm"
AGENT_PORT  = 8585

#
logger = None

#
def get_logger():
    global logger
    if not logger:
        handler = logging.StreamHandler()
        handler.setFormatter(logging.Formatter('%(message)s'))
        logger = logging.getLogger()
        logger.addHandler(handler)
        logger.setLevel(logging.DEBUG)
    return logger

#
def print_debug(text):
    print_method = print if not logger else logger.debug
    for line in text.split("\n"):
        print_method("[DEBUG] {}".format(line))

#
def print_info(text):
    print_method = print if not logger else logger.info
    for line in text.split("\n"):
        print_method(line)

#
class CloudStackApiClient:
    _MAX_RETRY = 180
    _ASYNC_INTERVAL = 5
    _INSTANCE = None

    @classmethod
    def get_instance(cls, zoneid, debug=False):
        if cls._INSTANCE is None or ( cls._INSTANCE and cls._INSTANCE.zoneid != zoneid ):
            cls._INSTANCE = cls(zoneid, debug)
        return cls._INSTANCE

    def __init__(self, zoneid, debug):
        self.zoneid = zoneid
        self._debug = debug
        self._config = read_config()
        self._cs = CloudStack(**self._config)
        self._vms = {}
        self._zones = {}
        self._lbs = {}
        self._templates = {}
        self._offerings = {}

    def _print_debug(self, text):
        if self._debug:
            print_debug(text)

    def _dump(self, data=None):
        if self._debug and data:
            print_debug(json.dumps(data, sort_keys=True, indent=2))

    def queryAsyncJobResult(self, jobid):
        for i in range(0, self._MAX_RETRY):
            job = self._cs.queryAsyncJobResult(jobid=jobid)
            if job['jobstatus'] == 1:
                self._dump(job)
                return job
            self._print_debug("wait for job: {} times".format(i + 1))
            time.sleep(self._ASYNC_INTERVAL)
        return None

    def _list(self, api_name, params):
        results = getattr(self._cs, api_name)(**params)
        self._dump(results)
        section = re.sub('^list(.+)s$', lambda m: m.group(1), api_name).lower()
        if section in results:
            return results[section]
        else:
            return []

    def listZones(self):
        return self._list("listZones", { "zoneid": self.zoneid })

    def listLoadBalancerRules(self):
        return self._list("listLoadBalancerRules", { "zoneid": self.zoneid })

    def listTemplates(self):
        return self._list("listTemplates", { "zoneid": self.zoneid, "templatefilter": "self" })

    def listServiceOfferings(self):
        return self._list("listServiceOfferings", {})

    def listVirtualMachines(self):
        return self._list("listVirtualMachines", { "zoneid": self.zoneid })

    def deployVirtualMachine(self, name, templateid, offeringid):
        result = self._cs.deployVirtualMachine(
            zoneid=self.zoneid,
            serviceofferingid=offeringid,
            templateid=templateid,
            name=name,
            displayname=name
        )
        job = self.queryAsyncJobResult(result['jobid'])
        if job is None or "jobresult" not in job or "virtualmachine" not in job["jobresult"]:
            return None
        uuid = job['jobresult']['virtualmachine']['id']
        self._vms[uuid] = { 'uuid': uuid, 'name': name }
        return self._vms[uuid]

    def destroyVirtualMachine(self, vmid):
        result = self._cs.destroyVirtualMachine(id=vmid, expunge=True)
        self.queryAsyncJobResult(result['jobid'])

    def assignToLoadBalancerRule(self, lbid, vmid):
        result = self._cs.assignToLoadBalancerRule(id=lbid, virtualmachineids=vmid)
        self.queryAsyncJobResult(result['jobid'])

    def removeFromLoadBalancerRule(self, lbid, vmid):
        result = self._cs.removeFromLoadBalancerRule(id=lbid, virtualmachineids=vmid)
        self.queryAsyncJobResult(result['jobid'])

    def _get_data(self, uuid, cache, method, params, force=False):
        if uuid not in cache or force:
            cache = {}
            for x in getattr(self, method)():
                cache[x['id']] = { p[0]:x[p[1]] for p in params }
        if uuid in cache:
            return cache[uuid]
        return None

    def get_vm_data(self, uuid, force=False):
        return self._get_data(
            uuid=uuid, cache=self._vms, method="listVirtualMachines",
            params=(('name', 'name'), ('uuid', 'id')),
            force=force
        )

    def get_zone_data(self, uuid, force=False):
        return self._get_data(
            uuid=uuid, cache=self._zones, method="listZones",
            params=(('name', 'name'), ('uuid', 'id')),
            force=force
        )

    def get_lb_data(self, uuid, force=False):
        return self._get_data(
            uuid=uuid, cache=self._lbs, method="listLoadBalancerRules",
            params=(('name', 'name'), ('uuid', 'id')),
            force=force
        )

    def get_template_data(self, uuid, force=False):
        return self._get_data(
            uuid=uuid, cache=self._templates, method="listTemplates",
            params=(('name', 'name'), ('uuid', 'id')),
            force=force
        )

    def get_offering_data(self, uuid, force=False):
        return self._get_data(
            uuid=uuid, cache=self._offerings, method="listServiceOfferings",
            params=(('name', 'name'), ('uuid', 'id')),
            force=force
        )

    def create_vm(self, name, lbid, templateid, offeringid):
        vm = self.deployVirtualMachine(name, templateid, offeringid)
        if vm:
            self.assignToLoadBalancerRule(lbid, vm['uuid'])
        return vm

    def remove_vm(self, vmid, lbid):
        self.removeFromLoadBalancerRule(lbid, vmid)
        self.destroyVirtualMachine(vmid)

#
class AutoScalingUsageCollector(threading.Thread):
    _TIMEOUT = 2

    def __init__(self, name, endpoint, info, usage, interval=INTERVAL, usage_count=USAGE_COUNT):
        super().__init__(name=name)
        self._event = threading.Event()
        self._endpoint = endpoint
        self._info = info
        self._interval = interval
        self._usage = usage
        self._usage_count = usage_count

    @property
    def event(self):
        return self._event

    @property
    def usage(self):
        return self._usage

    @property
    def active(self):
        return self._info['active']

    @property
    def failcount(self):
        return self._info['failcount']

    def run(self):
        interval = 0
        while not self._event.wait(timeout=interval):
            begin_time = time.time()
            usage = None
            try:
                result = requests.get(self._endpoint, timeout=self._TIMEOUT)
                usage = round(result.json()['usage'], 1)
                self._info['active'] = True
                self._info['failcount'] = 0
            except:
                self._info['failcount'] += 1
                if self._usage_count <= self._info['failcount']: 
                    self._info['active'] = False
            self._usage.append([time.strftime('%H:%M:%S', time.gmtime(begin_time)), usage])
            if len(self._usage) > self._usage_count:
                self._usage.pop(0)
            interval = self._interval - ( time.time() - begin_time )
            if interval < 0:
                interval = 0

#
class AutoScalingData:
    def __init__(self, file, debug=False):
        self._file = file
        self._debug = debug
        self.data = None

    def _print_debug(self, text):
        if self._debug:
            print_debug(text)

    def dump(self, data=None):
        if data is None:
            data = self.data
        if self._debug and data:
            print_debug(json.dumps(data, sort_keys=True, indent=2))

#
class AutoScalingConfig(AutoScalingData):
    # 0:Section, 1:OptionName, (2-0:Type, 2-1:Required, 2-2:Judge)
    _SCHEMA = {
        'cloudstack' : {
            'endpoint'            : (str,   True, None),
            'key'                 : (str,   True, None),
            'secret'              : (str,   True, None),
        },
        'tenant'     : {
            'zone_uuid'           : (str,   True, '_judge_zone'),
            'lb_rule_uuid'        : (str,   True, '_judge_lb'),
            'template_uuid'       : (str,   True, '_judge_template'),
            'serviceoffering_uuid': (str,   True, '_judge_offering'),
        },
        'vm'         : {
            'vm1_uuid'            : (str,   True, None),
        },
        'autoscaling': {
            'autoscaling_vm'      : (int,   True, None),
            'upper_limit'         : (float, True, None),
            'lower_limit'         : (float, True, None),
        },
    }

    def __init__(self, file, debug=False):
        super().__init__(file, debug)
        self._mtime = 0
        self._client = None
        self._ready = False

    def _judge_zone(self, uuid):
        return self._client.get_zone_data(uuid) is not None

    def _judge_lb(self, uuid):
        return self._client.get_lb_data(uuid) is not None

    def _judge_template(self, uuid):
        return self._client.get_template_data(uuid) is not None

    def _judge_offering(self, uuid):
        return self._client.get_offering_data(uuid) is not None

    def _judge(self):
        if self.data is None:
            self._print_debug("{} is empty".format(self._file))
            return False

        for section, params in self._SCHEMA.items():
            if section not in self.data:
                self._print_debug("Section {} is required".format(section))
                return False
            for name, options in params.items():
                if options[1]:
                    if name not in self.data[section]:
                        self._print_debug("Option {} => {} is required".format(section, name))
                        return False

        self._client = CloudStackApiClient.get_instance(
            zoneid=self.data['tenant']['zone_uuid'],
            debug=self._debug
        )
        for section, params in self._SCHEMA.items():
            for name, options in params.items():
                if options[2]:
                    if not getattr(self, options[2])(self.data[section][name]):
                        self._print_debug("Option {} => {} is incorrect".format(section, name))
                        return False
        return True

    def load(self):
        if not Path(self._file).is_file():
            self._print_debug("{} does not exist".format(self._file))
            self._ready = False
            return False

        current_mtime = os.path.getmtime(self._file)
        if current_mtime == self._mtime:
            self._print_debug("{} does not need to re-load".format(self._file))
            return False

        self._print_debug("{} loaded".format(self._file))
        conf = ConfigParser()
        conf.read(self._file)

        f = {
            None : lambda c, s, n: c.get(s, n),
            str  : lambda c, s, n: c.get(s, n),
            int  : lambda c, s, n: c.getint(s, n),
            float: lambda c, s, n: c.getfloat(s, n),
            bool : lambda c, s, n: c.getboolean(s, n),
        }

        self.data = {}
        for section in conf.sections():
            self.data[section] = {}
            for name in conf.options(section):
                option_type = None
                if section in self._SCHEMA and name in self._SCHEMA[section]:
                    option_type = self._SCHEMA[section][name][0]
                self.data[section][name] = f[option_type](conf, section, name)

        self.dump()
        self._ready = self._judge()
        self._mtime = current_mtime
        return True

    @property
    def ready(self):
        return self._ready

#
class AutoScalingStatus(AutoScalingData):
    _PICKLE_VERSION = 3
    _MAX_RETRY = 120
    _RETRY_INTERVAL = 5

    def __init__(self, file, debug=False):
        super().__init__(file, debug)
        self._agents = {}
        self._event_save = None

    def __del__(self):
        for agent in self._agents.values():
            agent.event.set()

    def _start_collector(self, uuid, name, info, usage, port=AGENT_PORT):
        if uuid not in self._agents:
            self._agents[uuid] = AutoScalingUsageCollector(
                name, "http://{}:{}/".format(name, port), info, usage)
        if not self._agents[uuid].is_alive():
            self._agents[uuid].start()

    def _stop_collector(self, uuid):
        if uuid in self._agents:
            self._agents.pop(uuid).event.set()

    def _wait_collector(self, uuid):
        for i in range(0, self._MAX_RETRY):
            if self._agents[uuid].active:
                return True
            time.sleep(self._RETRY_INTERVAL)
        return False

    def init_status(self):
        for uuid in self.data['vm']:
            self.data['status'][uuid][:] = []

    def remove_vm(self, uuid):
        self._stop_collector(uuid)
        self.data['vm'].pop(uuid)
        self.data['status'].pop(uuid)

    def add_vm(self, uuid, name, autoscaling=False, wait=False):
        self.data['vm'][uuid] = {
            'uuid'       : uuid,
            'name'       : name,
            'autoscaling': autoscaling,
            'active'     : False,
            'failcount'  : 0
        }
        self.data['status'][uuid] = []
        self._start_collector(uuid, name, self.data['vm'][uuid], self.data['status'][uuid])
        if wait:
            if not self._wait_collector(uuid):
                self.remove_vm(uuid)
                return False
        return True

    def load(self):
        self.data = {
            'vm'     : {},
            'status' : {},
            'average': 0.0,
            'info'   : { 'code': 200, 'message': None },
        }
        if Path(self._file).is_file():
            with open(self._file, 'rb') as fd:
                data = pickle.load(fd)
            if data and 'vm' in data:
                for uuid, vm in data['vm'].items():
                    self.add_vm(vm['uuid'], vm['name'], vm['autoscaling'])
        self.dump()
        return True

    def save(self):
        path = Path(self._file)
        tmpfile = None
        with NamedTemporaryFile(mode='wb', dir=path.parent, prefix=path.name, delete=False) as f:
            tmpfile = f.name
            pickle.dump(self.data, f, protocol=self._PICKLE_VERSION)
        if tmpfile:
            os.rename(tmpfile, self._file)
            self.dump()

    @property
    def is_constant_save(self):
        return self._event_save is not None

    def start_constant_save(self):
        def run():
            while not self._event_save.wait(timeout=15):
                self.save()
            self._event_save = None

        if not self.is_constant_save:
            thread = threading.Thread(target=run)
            self._event_save = threading.Event()
            thread.start()

    def stop_constant_save(self):
        if self.is_constant_save:
            self._event_save.set()

    def set_info(self, code, **kwargs):
        c = catalog.CATALOG[code]
        self.data['info'] = {
            'code': code,
            'message': c.format(**kwargs) if c else c
        }

#
class AutoScalingController:
    def __init__(self, config_file, status_file, prefix=VM_PREFIX, debug=False):
        self._debug = debug
        self._client = None
        self._prefix = prefix
        self._config = AutoScalingConfig(config_file, self._debug)
        self._status = AutoScalingStatus(status_file, self._debug)

    def _print_debug(self, text):
        if self._debug:
            print_info("[DEBUG] {}".format(text))

    def _get_cloudstack(self):
        self._client = CloudStackApiClient.get_instance(
            zoneid=self._config.data['tenant']['zone_uuid'],
            debug=self._debug
        )

    def _available_vm(self):
        return {
            uuid: v for uuid, v in self._status.data['vm'].items()
                if v is not None and v['active']
        }

    def _autoscaling_vm(self):
        return [
            v for uuid, v in self._status.data['vm'].items()
                if v is not None and v['autoscaling']
        ]

    def _stable_vm(self):
        return [
            v for uuid, v in self._status.data['vm'].items()
                if v is not None and not v['autoscaling']
        ]

    def load_config(self):
        updated = self._config.load()
        self._print_debug("ready={}, updated={}".format(self._config.ready, updated))
        if not self._config.ready:
            if self._status.is_constant_save:
                self._status.stop_constant_save()
                self._status.set_info(catalog.ERROR_CONFIG)
                self.save_status()
            return False
        if updated:
            self._get_cloudstack()
            # new stable VM
            stables = self._config.data['vm'].values()
            for uuid in stables:
                if uuid in self._status.data['vm']:
                    continue
                vm = self._get_vm_data(uuid)
                if vm:
                    self._status.add_vm(**vm, autoscaling=False)
            # leave stable VM
            for vm in self._stable_vm():
                if vm['uuid'] not in stables:
                    self._status.remove_vm(vm['uuid'])
        self._status.set_info(catalog.OK)
        self._status.start_constant_save()
        return True

    def load_status(self):
        self._status.load()

    def save_status(self):
        self._status.save()

    def create_vm(self):
        vms = [ v['name'] for v in self._autoscaling_vm() ]
        if self._config.data['autoscaling']['autoscaling_vm'] <= len(vms):
            return
        for i in range(1, 100):
            name = "{}{:02d}".format(self._prefix, i)
            if name not in vms:
                break
        self._status.set_info(catalog.OK_CREATING, name=name)
        vm = self._client.create_vm(
            name,
            self._config.data['tenant']['lb_rule_uuid'],
            self._config.data['tenant']['template_uuid'],
            self._config.data['tenant']['serviceoffering_uuid']
        )
        if vm is None:
            self._status.set_info(catalog.ERROR_CREATE, name=name)
            print_info("Error: Failed to create a new vm: name={}".format(name))
            return
        uuid = vm['uuid']
        if self._status.add_vm(**vm, autoscaling=True, wait=True):
            self._status.init_status()
            self._status.set_info(catalog.OK_CREATED, name=name)
            print_info("Create new vm: name={}, uuid={}".format(name, uuid))
        else:
            self._client.remove_vm(uuid, self._config.data['tenant']['lb_rule_uuid'])

    def remove_vm(self, uuid=None):
        if uuid is None:
            vms = sorted(self._autoscaling_vm(), key=lambda x: x['name'])
            if len(vms) == 0:
                return
            for vm in vms:
                if not vm['active']:
                    uuid = vm['uuid']
                    name = vm['name']
                    break
            else:
                name = vms[-1]['name']
                uuid = vms[-1]['uuid']
        else:
            name = self._status.data['vm'][uuid]['name']
        self._status.set_info(catalog.OK_REMOVING, name=name)
        self._client.remove_vm(uuid, self._config.data['tenant']['lb_rule_uuid'])
        self._status.remove_vm(uuid)
        self._status.init_status()
        self._status.set_info(catalog.OK_REMOVED, name=name)
        print_info("remove the vm: name={}, uuid={}".format(name, uuid))

    def clean_vm(self):
        for vm in self._autoscaling_vm():
            if not vm['active']:
                self.remove_vm(vm['uuid'])

    def _get_vm_data(self, uuid):
        vm = self._client.get_vm_data(uuid)
        print_info("uuid={}, data={}".format(uuid, vm))
        return vm

    def _get_vm_usage(self, uuid):
        usage = [ x for x in self._status.data['status'][uuid] if x[1] is not None ]
        print_info("uuid={}, usage={}".format(uuid, usage))
        return usage

    def calculate_usage(self):
        total_usage = 0.0
        total_count = 0
        vms = self._available_vm()
        for uuid, vm in vms.items():
            target = self._get_vm_usage(uuid)
            total_count += len(target)
            total_usage += sum([ x[1] for x in target ])

        if total_count == 0:
            self._status.set_info(catalog.OK_NO_DATA)
            self._print_debug("There's not any usage")
            return

        average = round(total_usage / total_count, 1)
        self._status.set_info(catalog.OK_AVERAGE, average=average)
        if total_count == ( USAGE_COUNT * len(vms) ):
            if average >= self._config.data['autoscaling']['upper_limit']:
                self.create_vm()
            if average <= self._config.data['autoscaling']['lower_limit']:
                self.remove_vm()
        self._status.data['average'] = average

    def run(self):
        self.load_status()
        while True:
            begin_time = time.time()
            if self.load_config():
                self.clean_vm()
                self.calculate_usage()
            interval = INTERVAL - ( time.time() - begin_time )
            if interval > 0:
                time.sleep(interval)


if __name__ == '__main__':                        
    # Options
    parser = ArgumentParser()
    parser.add_argument("-d", "--debug", action="store_true", default=False, help="Debug mode")
    parser.add_argument("-c", "--config", type=str, default=CONFIG_FILE, help="Config file")
    parser.add_argument("-s", "--status", type=str, default=STATUS_FILE, help="Status file")
    parser.add_argument("-P", "--prefix", type=str, default=VM_PREFIX, help="VM prefix. Default: {}".format(VM_PREFIX))
    args = parser.parse_args()

    #
    logger = get_logger()

    try:
        # Run AutoScalingController
        controller = AutoScalingController(args.config, args.status, args.prefix, args.debug)
        controller.run()
    except KeyboardInterrupt:
        del controller
        time.sleep(0.1)
