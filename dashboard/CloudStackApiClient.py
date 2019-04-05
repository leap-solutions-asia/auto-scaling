import json
from cs import read_config, CloudStack

class CloudStackApiClient:
    _INSTANCE = None

    @classmethod
    def get_instance(cls):
        if cls._INSTANCE is None:
            cls._INSTANCE = cls()
        return cls._INSTANCE

    def __init__(self, key=None, secret=None, endpoint=None):
        if key is None or secret is None or endpoint is None:
            self._config = read_config()
            self._cs = CloudStack(**self._config)
        else:
            self._cs = CloudStack(key=key, secret=secret, endpoint=endpoint)
        self.vms = []
        self.zones = []
        self.lbs = []
        self.tps = []
        self.nws = []
        self.svs = []
    
    def listVirtualMachines(self, force=False):
        if force or len(self.vms) == 0:
            vms = self._cs.listVirtualMachines()
            self.vms = [ (vm['id'], vm['name']) for vm in vms['virtualmachine'] ]
        return self.vms
    
    def listZones(self, force=False):
        if force or len(self.zones) == 0:
            zones = self._cs.listZones()
            self.zones = [ (zone['id'], zone['name']) for zone in zones['zone'] ]
        return self.zones

    def listLoadBalancerRules(self, force=False):
        if force or len(self.lbs) == 0:
            lbs = self._cs.listLoadBalancerRules()
            self.lbs = [ (lb['id'], lb['name']) for lb in lbs['loadbalancerrule'] ]
        return self.lbs

    def listTemplates(self, force=False):
        if force or len(self.tps) == 0:
            tps = self._cs.listTemplates(templatefilter="self")
            self.tps = [ (tp['id'], tp['name']) for tp in tps['template'] ]
        return self.tps
        
    def listNetworks(self, force=False):
        if force or len(self.nws) == 0:
            nws = self._cs.listNetworks()
            self.nws = [ (nw['id'], nw['name']) for nw in nws['network'] ]
        return self.nws
		
    def listServiceOfferings(self, force=False):
        if force or len(self.svs) == 0:
            svs = self._cs.listServiceOfferings()
            self.svs = [ (sv['id'], sv['name']) for sv in svs['serviceoffering'] ]
        return self.svs
    
    def _get_name(self, data, uuid):
        for x in data:
            if uuid == x[0]:
                return x[1]
        return None

    def get_vm_name(self, uuid):
        name = self._get_name(self.vms, uuid)
        if name is None:
            self.listVirtualMachines(force=True)
            name = self._get_name(self.vms, uuid)
        return name
        
    def get_zone_name(self, uuid):
        name = self._get_name(self.zones, uuid)
        if name is None:
            self.listZones(force=True)
            name = self._get_name(self.zones, uuid)
        return name
        
    def get_lb_name(self, uuid):
        name = self._get_name(self.lbs, uuid)
        if name is None:
            self.listLoadBalancerRules(force=True)
            name = self._get_name(self.lbs, uuid)
        return name
        
    def get_tp_name(self, uuid):
        name = self._get_name(self.tps, uuid)
        if name is None:
            self.listTemplates(force=True)
            name = self._get_name(self.tps, uuid)
        return name
        
    def get_nw_name(self, uuid):
        name = self._get_name(self.nws, uuid)
        if name is None:
            self.listNetworks(force=True)
            name = self._get_name(self.nws, uuid)
        return name
        
    def get_sv_name(self, uuid):
        name = self._get_name(self.svs, uuid)
        if name is None:
            self.listServiceOfferings(force=True)
            name = self._get_name(self.svs, uuid)
        return name
