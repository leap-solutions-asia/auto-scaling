import configparser
import os
from tempfile import NamedTemporaryFile

cloudstack_file = "/auto-scaling/cloudstack.ini"

class CloudStackConfig:
    def __init__(self):
        self._conf = configparser.ConfigParser()
        if os.path.exists(cloudstack_file):
            self._conf.read(cloudstack_file)
    
    def create_configfile(self):
        if not os.path.exists(cloudstack_file):
            self._conf.write(open(cloudstack_file, 'w'))
    
    def update_configfile(self):
        dirname, basename = os.path.split(cloudstack_file)
        with NamedTemporaryFile(mode='w', dir=dirname, prefix=basename, delete=False) as f:
            tmpfile = f.name
            with open(tmpfile, "w") as config_file:
                self._conf.write(config_file)
            if tmpfile:
                os.rename(tmpfile, cloudstack_file)
    
    def get_secret(self):
        data = None
        if self.has_cloudstack_section():
            data = self._conf.get("cloudstack", "secret")
        return data
        
    def get_key(self):
        data = None
        if self.has_cloudstack_section():
            data = self._conf.get("cloudstack", "key")
        return data
        
    def get_endpoint(self):
        data = None
        if self.has_cloudstack_section():
            data = self._conf.get("cloudstack", "endpoint")
        return data
    
    def get_lb_rule_uuid(self):
        data = None
        if self.has_tenant_section():
            data = self._conf.get("tenant", "lb_rule_uuid")
        return data
        
    def get_zone_uuid(self):
        data = None
        if self.has_tenant_section():
            data = self._conf.get("tenant", "zone_uuid")
        return data
        
    def get_template_uuid(self):
        data = None
        if self.has_tenant_section():
            data = self._conf.get("tenant", "template_uuid")
        return data
        
    def get_nw_uuid(self, nw):
        data = None
        if self.has_tenant_section():
            data = self._conf.get("tenant", nw)
        return data
        
    def get_serviceoffering_uuid(self):
        data = None
        if self.has_tenant_section():
            data = self._conf.get("tenant", "serviceoffering_uuid")
        return data
        
    def get_autoscaling_vm(self):
        data = None
        if self.has_autoscaling_section():
            data = self._conf.get("autoscaling", "autoscaling_vm")
        return data
        
    def get_upper_limit(self):
        data = None
        if self.has_autoscaling_section():
            data = self._conf.get("autoscaling", "upper_limit")
        return data
        
    def get_lower_limit(self):
        data = None
        if self.has_autoscaling_section():
            data = self._conf.get("autoscaling", "lower_limit")
        return data
        
    def get_vm_uuid(self, vm):
        data = None
        if self.has_vm_section():
            data = self._conf.get("vm", vm)
        return data
    
    def set_secret(self, data):
        if not self.has_cloudstack_section():
            self.add_cloudstack_section()
        uuid = self._conf.set("cloudstack", "secret", data)
        
    def set_key(self, data):
        if not self.has_cloudstack_section():
            self.add_cloudstack_section()
        uuid = self._conf.set("cloudstack", "key", data)
        
    def set_endpoint(self, data):
        if not self.has_cloudstack_section():
            self.add_cloudstack_section()
        uuid = self._conf.set("cloudstack", "endpoint", data)
    
    def set_lb_rule_uuid(self, data):
        if not self.has_tenant_section():
            self.add_tenant_section()
        uuid = self._conf.set("tenant", "lb_rule_uuid", data)
        
    def set_zone_uuid(self, data):
        if not self.has_tenant_section():
            self.add_tenant_section()
        uuid = self._conf.set("tenant", "zone_uuid", data)
        
    def set_template_uuid(self, data):
        if not self.has_tenant_section():
            self.add_tenant_section()
        uuid = self._conf.set("tenant", "template_uuid", data)
        
    def set_nw(self, item, data):
        if not self.has_tenant_section():
            self.add_tenant_section()
        uuid = self._conf.set("tenant", item, data)
        
    def set_serviceoffering_uuid(self, data):
        if not self.has_tenant_section():
            self.add_tenant_section()
        uuid = self._conf.set("tenant", "serviceoffering_uuid", data)
        
    def set_autoscaling_vm(self, data):
        if not self.has_autoscaling_section():
            self.add_autoscaling_section()
        uuid = self._conf.set("autoscaling", "autoscaling_vm", str(data))
    
    def set_upper_limit(self, data):
        if not self.has_autoscaling_section():
            self.add_autoscaling_section()
        uuid = self._conf.set("autoscaling", "upper_limit", str(data))
        
    def set_lower_limit(self, data):
        if not self.has_autoscaling_section():
            self.add_autoscaling_section()
        uuid = self._conf.set("autoscaling", "lower_limit", str(data))
        
    def set_vm(self, item, data):
        if not self.has_vm_section():
            self.add_vm_section()
        uuid = self._conf.set("vm", item, data)
        
    def has_vm_section(self):
        if self._conf.has_section("vm"):
            return True
        return False
        
    def has_tenant_section(self):
        if self._conf.has_section("tenant"):
            return True
        return False
        
    def has_autoscaling_section(self):
        if self._conf.has_section("autoscaling"):
            return True
        return False
        
    def has_cloudstack_section(self):
        if self._conf.has_section("cloudstack"):
            return True
        return False

    def add_vm_section(self):
        self._conf.add_section("vm")
    
    def add_cloudstack_section(self):
        self._conf.add_section("cloudstack")
        
    def add_tenant_section(self):
        self._conf.add_section("tenant")
        
    def add_autoscaling_section(self):
        self._conf.add_section("autoscaling")

    def remove_cloudstack_section(self):
        self._conf.remove_section("cloudstack")
        
    def remove_tenant_section(self):
        self._conf.remove_section("tenant")
        
    def remove_autoscaling_section(self):
        self._conf.remove_section("autoscaling")
        
    def remove_vm_section(self):
        self._conf.remove_section("vm")
        
    def get_vm_list(self):
        data = None
        if self.has_vm_section():
            data = self._conf.options("vm")
        return data
    
    def get_tenant_list(self):
        data = None
        if self.has_tenant_section():
            data = self._conf.options("tenant")
        return data
        
    def get_networks(self):
        data = []
        if self.has_tenant_section():
            for nw in self.get_tenant_list():
                if nw.startswith("network"):
                    uuid = self.get_nw_uuid(nw)
                    data.append((uuid))
        return data
