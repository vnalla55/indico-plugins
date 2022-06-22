# This file is part of the Indico plugins.
# Copyright (C) 2002 - 2022 CERN
#
# The Indico plugins are free software; you can redistribute
# them and/or modify them under the terms of the MIT License;
# see the LICENSE file for more details.

from flask_pluginengine import render_plugin_template
from wtforms.fields import StringField, URLField
from wtforms.validators import DataRequired, Optional

from indico.core.plugins import IndicoPlugin, url_for_plugin
from indico.modules.events.payment import (PaymentEventSettingsFormBase, PaymentPluginMixin,
                                           PaymentPluginSettingsFormBase)
from indico.util.string import remove_accents, str_to_ascii
from indico.web.forms.validators import UsedIf

from indico_payment_touchnet import _
from indico_payment_touchnet.blueprint import blueprint
from indico_payment_touchnet.util import validate_business

#Mayuresh
import base64
from hashlib import md5
from base64 import standard_b64encode

class PluginSettingsForm(PaymentPluginSettingsFormBase):
    url = URLField(_('API URL'), [DataRequired()], description=_('URL of the TouchNet HTTP API.'))  
    

class EventSettingsForm(PaymentEventSettingsFormBase):
    site_id = StringField(_('SITE ID'), [DataRequired()], description=_('Site ID.'))
    validation_key = StringField(_('Validation Key'), [DataRequired()], description=_('Validation Key.'))
    posting_key = StringField(_('Posting Key'), [DataRequired()], description=_('Posting Key.'))
   

class TouchNetPaymentPlugin(PaymentPluginMixin, IndicoPlugin):
    """TouchNet

    Provides a payment method using the TouchNet IPN API.
    """


    configurable = True
    settings_form = PluginSettingsForm
    event_settings_form = EventSettingsForm
    default_settings = {'method_name': 'TouchNet',
                        'url': 'https://test.secure.touchnet.net:8443/C20210test_upay/web/index.jsp'
                       }
    
    default_event_settings = {'enabled': False,
                            'method_name': None,
                            'site_id':"58",
                            'posting_key':"pG1eT6NxrGnyjbuY",
                            'validation_key':"eZ22UJi0Uv0ghVSI"
                            }

    def init(self):
        super().init()
        self.template_hook('event-manage-payment-plugin-before-form', self._get_encoding_warning)

    @property
    def logo_url(self):
        return url_for_plugin(self.name + '.static', filename='images/logo.png')

    def get_blueprints(self):
        return blueprint

    def adjust_payment_form_data(self, data):
        event = data['event']
        registration = data['registration']
        data['item_name'] = '{}: registration for {}'.format(
            str_to_ascii(remove_accents(registration.full_name)),
            str_to_ascii(remove_accents(event.title))
        )
        data['return_url'] = url_for_plugin('payment_touchnet.success', registration.locator.uuid, _external=True)
        data['cancel_url'] = url_for_plugin('payment_touchnet.cancel', registration.locator.uuid, _external=True)
        data['notify_url'] = url_for_plugin('payment_touchnet.notify', registration.locator.uuid, _external=True)
        
        #Mayuresh
        ext_trans_id = str(data['event_id']) + "_" + str(data['registration_id']) #"abc123"
        validation_key =  str(self.default_event_settings['validation_key']) # "eZ22UJi0Uv0ghVSI"
        hash_string = validation_key + ext_trans_id + str(data['amount']) #validation_key + transaction_id + amount
        indico_hash = md5()
        indico_hash.update(hash_string.encode())
        byte_hash = standard_b64encode(indico_hash.digest())
        string_hash = str(byte_hash.decode("utf-8"))
        data['encoded_validation_key'] =  string_hash #"Dakx8ZmcayS7FJbC/S+npQ=="
        data['ext_trans_id'] =  ext_trans_id


    def _get_encoding_warning(self, plugin=None, event=None):
        if plugin == self:
            return render_plugin_template('event_settings_encoding_warning.html')
