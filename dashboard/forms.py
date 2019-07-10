import json
import configparser

from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, BooleanField, SelectField, SelectMultipleField, IntegerField
from wtforms.validators import DataRequired, Length, Email, EqualTo, NumberRange, URL, InputRequired, ValidationError

from cs import read_config, CloudStack
from CloudStackApiClient import CloudStackApiClient
from timezone import TIMEZONE, DEFAULT_TIMEZONE

class AutoScalingSelectField(SelectField):
    def iter_choices(self):
        current_value = self.data if self.data is not None else self.coerce(self.default)
        for value, label in self.choices:
            yield (value, label, self.coerce(value) == current_value)
            
class AutoScalingSelectMultipleField(SelectMultipleField):
    def iter_choices(self):
        current_value = self.data if self.data is not None else self.coerce(self.default)
        for value, label in self.choices:
            yield (value, label, self.coerce(value) in current_value)

class EditSettingsForm(FlaskForm):
    template_uuid = AutoScalingSelectField('Template')
    nws = AutoScalingSelectMultipleField('Network List', choices=[])
    lb_rule_uuid = AutoScalingSelectField('Loadbalancer Rule')
    serviceoffering_uuid = AutoScalingSelectField('Service Offering')
    zone_uuid = AutoScalingSelectField('Zone')
    autoscaling_vm = IntegerField('Maximum number of instances', validators=[
        InputRequired(), 
        NumberRange(min=1, max=99, message='A number must be between (1-99)')
    ])
    upper_limit = IntegerField('Threshold of Scale-up', validators=[
        InputRequired(), 
        NumberRange(min=1, max=99, message='A number must be between (1-99)')
    ])
    lower_limit = IntegerField('Threshold of Scale-down', validators=[
        InputRequired(), 
        NumberRange(min=1, max=99, message='A number must be between (1-99)')
    ])
    vms =   AutoScalingSelectMultipleField('VM List', choices=[])
    timezone = AutoScalingSelectField('Timezone', default=DEFAULT_TIMEZONE, choices=TIMEZONE)
    submit = SubmitField('Update')
    
    def validate_vms(self, extra):
        if len(self.vms.data) < 1:
            msg = 'Please select a single VM at least!'
            self.vms.errors.append(msg)
            return False
        return True
    
    def validate_nws(self, extra):
        if len(self.nws.data) < 1:
            msg = 'Please select a single network at least!'
            self.nws.errors.append(msg)
            return False
        return True
    
    def validate_lower_limit(self, extra):
        if type(self.lower_limit.data) is not int or type(self.upper_limit.data) is not int:
            return False
        if not self.lower_limit.data < self.upper_limit.data:
            msg = 'Lower_limit must be lower than Upper_limit'
            self.lower_limit.errors.append(msg)
            return False
        return True    

class EditCredentialForm(FlaskForm):
    key = StringField('API Key', validators=[
        DataRequired(), 
        Length(min=2, max=255)
    ])
    secret = StringField('API Secret', validators=[
        DataRequired(), 
        Length(min=2, max=255)
    ])
    endpoint = StringField('API Endpoint', validators=[
        InputRequired(), 
        Length(min=2, max=255), URL(require_tld=False)
    ])
    submit = SubmitField('Update')

    def validate_endpoint(self, extra):
        try:
            endpoint = self.endpoint.data 
            key = self.key.data
            secret = self.secret.data
            cs = CloudStackApiClient(key, secret, endpoint)
            zones = cs.listZones()
            if not len(zones) >= 1:
                raise Exception('Your API credential is invalid, Please recheck!')
        except:
            msg = 'Your API credential is invalid, Please recheck!'
            self.endpoint.errors.append(msg)
            return False
        return True
    
class CredentialForm(FlaskForm):
    submit = SubmitField('Edit')

class SettingsForm(FlaskForm):
    submit = SubmitField('Edit')
