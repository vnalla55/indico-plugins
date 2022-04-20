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

import hashlib
import base64

class PluginSettingsForm(PaymentPluginSettingsFormBase):
    url = URLField(_('API URL'), [DataRequired()], description=_('URL of the TouchNet HTTP API.'))

class EventSettingsForm(PaymentEventSettingsFormBase):
    siteid = StringField(_('SITE ID'), [DataRequired()], description=_('Site ID.'))
    validationkey = StringField(_('Validation Key'), [DataRequired()], description=_('Validation Key.'))
    postingkey = StringField(_('Posting Key'), [DataRequired()], description=_('Posting Key.'))                        
   

class TouchNetPaymentPlugin(PaymentPluginMixin, IndicoPlugin):
    """TouchNet

    Provides a payment method using the TouchNet IPN API.
    """
    configurable = True
    settings_form = PluginSettingsForm
    event_settings_form = EventSettingsForm
    default_settings = {'method_name': 'TouchNet',
                        'url': '',
                       }
                        
    default_event_settings = {'enabled': False,
                              'method_name': None,
                              'siteid':"58",
                              'validationkey': "eZ22UJi0Uv0ghVSI",
                              'postingkey':"pG1eT6NxrGnyjbuY",
                            }

    def getvalidationkey(self):
        return self.default_event_settings.validationkey

    def gethash_validationkey(self, data, amount):
        registration = data['registration']
        amt = '%.2f' % amount
        extId = "c%sr%s" % (registration.event_id, registration.id)
        m = hashlib.md5()
        m.update('%s%s%s' % (self.getvalidationkey(), extId, amt))
        vk = base64.b64encode(m.digest())
        return vk

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

    def _get_encoding_warning(self, plugin=None, event=None):
        if plugin == self:
            return render_plugin_template('event_settings_encoding_warning.html')
