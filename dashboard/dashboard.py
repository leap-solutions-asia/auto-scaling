import os
import re
import pickle

from flask import Flask, render_template, url_for, flash, redirect, session
from forms import SettingsForm, CredentialForm, EditCredentialForm, EditSettingsForm

from CloudStackApiClient import CloudStackApiClient
from CloudStackConfig import CloudStackConfig, cloudstack_file

app = Flask(__name__)

app.config['SECRET_KEY'] = '04f38b5709e0425f716a3e630b01085b'
autoscaling_file = "/auto-scaling/autoscaling.status"

@app.route('/')
@app.route("/dashboard")
def dashboard():
    conf = CloudStackConfig()
    if not conf.has_cloudstack_section():
        session.pop('_flashes', None)
        flash(f'Please input Cloudstack credential first', 'success')
        return redirect(url_for('editcredential'))
        
    if not conf.has_tenant_section():
        flash(f'Please complete the settings!', 'success')
        return redirect(url_for('editsettings'))
    
    if not conf.has_autoscaling_section():
        flash(f'Please complete the settings', 'success')
        return redirect(url_for('editsettings'))
       
    params = {}
    params["title"] = 'Autoscale Dashboard'
    params["labels"] = None
    params["datasets"] = None
    params["autoscaling_data"] = None
    
    if not os.path.exists(autoscaling_file):
        params["message"] = 'Autoscaling file does not exist, Please try to reload in minutes'
    
    else:
        with open(autoscaling_file, 'rb') as fd:
            autoscaling_data = pickle.load(fd)
    
        labels = [] 
        for uuid, value in autoscaling_data['status'].items():
            labels = [ x[0] for x in value ]
            break
    
        datasets = []
        for uuid, value in autoscaling_data['status'].items():
            color = re.sub('^[^-]*([^-])-[^-]*([^-])-[^-]*([^-])-[^-]*([^-])-[^-]*([^-]{2})$', '#\\1\\2\\3\\4\\5', uuid)
            datasets.append({
                "label": autoscaling_data['vm'][uuid]['name'],
                "borderColor": color,
                "fill": False,
                "data": [ x[1] for x in value ]
            })

        params["labels"] = labels
        params["datasets"] = datasets
        params["autoscaling_data"] = autoscaling_data
    
    return render_template('dashboard.html', **params)

@app.route("/credential", methods=['GET', 'POST'])
def credential():
    conf = CloudStackConfig()
    if not conf.has_cloudstack_section():
        flash(f'Please input Cloudstack credential first', 'success')
        return redirect(url_for('editcredential'))

    form = CredentialForm()
    
    if form.validate_on_submit():
        return redirect(url_for('editcredential'))
    
    cs_secret = conf.get_secret()
    cs_key = conf.get_key()
    cs_endpoint = conf.get_endpoint()
    
    params = {}
    params["title"] = 'Credential'
    params["form"] = form
    params["cs_secret"] = cs_secret
    params["cs_key"] = cs_key
    params["cs_endpoint"] = cs_endpoint
    
    return render_template('credential.html', **params)
    
@app.route("/editcredential", methods=['GET', 'POST'])
def editcredential():
    form = EditCredentialForm()
    conf = CloudStackConfig()
    
    if form.validate_on_submit():
        if not conf.has_cloudstack_section():
            conf.add_cloudstack_section()
        
        if conf.has_tenant_section():
            conf.remove_tenant_section()

        if conf.has_autoscaling_section():
            conf.remove_autoscaling_section()
            
        if conf.has_vm_section():
            conf.remove_vm_section()
            
        conf.set_secret(form.secret.data)
        conf.set_key(form.key.data)
        conf.set_endpoint(form.endpoint.data)
        conf.update_configfile()

        flash(f'Credential updated for {form.key.data}!, Please update autoscale settings', 'success')
        return redirect(url_for('editsettings'))
            
    params = {}
    if conf.get_secret():
        params["cs_secret"] = conf.get_secret()
    if conf.get_key():
        params["cs_key"] = conf.get_key()
    if conf.get_endpoint():
        params["cs_endpoint"]= conf.get_endpoint()
    params["title"] = 'Edit Credential'
    params["form"] = form
    return render_template('editcredential.html', **params)
	
@app.route("/settings", methods=['GET', 'POST'])
def settings():
    conf = CloudStackConfig()
    if not conf.has_cloudstack_section():
        flash(f'Please input Cloudstack credential first', 'success')
        return redirect(url_for('editcredential'))
        
    if not conf.has_tenant_section():
        flash(f'Please complete the settings', 'success')
        return redirect(url_for('editsettings'))
    
    if not conf.has_autoscaling_section():
        flash(f'Please complete the settings', 'success')
        return redirect(url_for('editsettings'))

    form = SettingsForm()
    cs = CloudStackApiClient.get_instance()
    
    if form.validate_on_submit():
        return redirect(url_for('editsettings'))
    
    tenant_lb_rule_uuid = conf.get_lb_rule_uuid()
    tenant_zone_uuid = conf.get_zone_uuid()
    tenant_template_uuid = conf.get_template_uuid()
    tenant_serviceoffering_uuid = conf.get_serviceoffering_uuid()
    autoscaling_autoscaling_vm = conf.get_autoscaling_vm()
    autoscaling_upper_limit = conf.get_upper_limit()
    autoscaling_lower_limit = conf.get_lower_limit()
    
    tenant_zone_name = cs.get_zone_name(tenant_zone_uuid)
    tenant_lb_rule_name = cs.get_lb_name(tenant_lb_rule_uuid)
    tenant_template_name = cs.get_tp_name(tenant_template_uuid)
    tenant_serviceoffering_name = cs.get_sv_name(tenant_serviceoffering_uuid)
    
    networks_name_list = []
    if conf.has_tenant_section():
        for nw_uuid in conf.get_networks():
            nw_name = cs.get_nw_name(nw_uuid)
            networks_name_list.append(nw_name)
    
    vms_name_list = []
    if conf.has_vm_section():
        for vm in conf.get_vm_list():
            vm_uuid = conf.get_vm_uuid(vm)
            vm_name = cs.get_vm_name(vm_uuid)
            vms_name_list.append(vm_name)
    
    params = {}
    params["title"] = 'Settings'
    params["form"] = form
    params["tenant_zone_name"] = tenant_zone_name
    params["tenant_lb_rule_name"] = tenant_lb_rule_name
    params["tenant_template_name"] = tenant_template_name
    params["networks_name_list"] = networks_name_list
    params["tenant_serviceoffering_name"] = tenant_serviceoffering_name
    params["autoscaling_autoscaling_vm"] = autoscaling_autoscaling_vm
    params["autoscaling_upper_limit"] = autoscaling_upper_limit
    params["autoscaling_lower_limit"] = autoscaling_lower_limit
    params["vms_name_list"] = vms_name_list

    return render_template('settings.html', **params)

@app.route("/editsettings", methods=['GET', 'POST'])
def editsettings():    
    form = EditSettingsForm()
    cs = CloudStackApiClient.get_instance()
    messages = []
    form.template_uuid.choices = cs.listTemplates(force=True)
    if not form.template_uuid.choices:
        form.template_uuid.errors = ['Please create templates first!']
        messages.append({'category':'danger','content':'Please create templates first!'})
    form.nws.choices = cs.listNetworks(force=True)
    form.lb_rule_uuid.choices = cs.listLoadBalancerRules(force=True)
    if not form.lb_rule_uuid.choices:
        form.lb_rule_uuid.errors = ['Please create LB rules first!']
        messages.append({'category':'danger','content':'Please create LB Rules first!'})
    form.serviceoffering_uuid.choices = cs.listServiceOfferings(force=True)
    form.zone_uuid.choices = cs.listZones(force=True)
    form.vms.choices = cs.listVirtualMachines(force=True)
    conf = CloudStackConfig()
    
    if form.validate_on_submit():
        if conf.has_tenant_section():
            conf.remove_tenant_section()
        conf.add_tenant_section()
        conf.set_zone_uuid(form.zone_uuid.data)
        conf.set_lb_rule_uuid(form.lb_rule_uuid.data)
        conf.set_template_uuid(form.template_uuid.data)
        conf.set_serviceoffering_uuid(form.serviceoffering_uuid.data)
        for num, uuid in enumerate(form.nws.data, start=1):
            conf.set_nw("network{}_uuid".format(num), uuid)
            
        if conf.has_autoscaling_section():
            conf.remove_autoscaling_section()
        conf.add_autoscaling_section()
        conf.set_autoscaling_vm(form.autoscaling_vm.data)
        conf.set_upper_limit(form.upper_limit.data)
        conf.set_lower_limit(form.lower_limit.data)
        
        if conf.has_vm_section():
            conf.remove_vm_section()
        conf.add_vm_section()
        for num, uuid in enumerate(form.vms.data, start=1):
            conf.set_vm("vm{}_uuid".format(num), uuid)
    
        conf.update_configfile()
            
        flash(f'Settings has been updated!', 'success')
        return redirect(url_for('settings'))
        
    params = {}
    if conf.has_tenant_section() and conf.has_autoscaling_section():
        tenant_zone_uuid = conf.get_zone_uuid()
        tenant_lb_rule_uuid = conf.get_lb_rule_uuid()
        tenant_template_uuid = conf.get_template_uuid()
        tenant_serviceoffering_uuid = conf.get_serviceoffering_uuid()
        nws = conf.get_networks()
        autoscaling_autoscaling_vm = conf.get_autoscaling_vm()
        autoscaling_upper_limit = conf.get_upper_limit()
        autoscaling_lower_limit = conf.get_lower_limit()
        vms = []
        if conf.has_vm_section():
            for vm in conf.get_vm_list():
                vms.append(conf.get_vm_uuid(vm))

        form.zone_uuid.default = tenant_zone_uuid
        form.template_uuid.default = tenant_template_uuid
        form.nws.default = nws
        form.serviceoffering_uuid.default = tenant_serviceoffering_uuid
        form.lb_rule_uuid.default = tenant_lb_rule_uuid
        form.vms.default = vms
        form.process()
      
        params = {
            "tenant_zone_uuid": tenant_zone_uuid, 
            "tenant_lb_rule_uuid": tenant_lb_rule_uuid,
            "tenant_template_uuid": tenant_template_uuid,
            "nws": nws,
            "tenant_serviceoffering_uuid": tenant_serviceoffering_uuid,
            "autoscaling_autoscaling_vm": autoscaling_autoscaling_vm,
            "autoscaling_upper_limit": autoscaling_upper_limit,
            "autoscaling_lower_limit": autoscaling_lower_limit,
            "vms": vms,
        }

    params["title"] = 'Edit Settings'
    params["form"] = form
    params["messages"] = messages
    return render_template('editsettings.html', **params)

if __name__ == '__main__':                        
    app.run(host="0.0.0.0", port=8080, debug=True)
