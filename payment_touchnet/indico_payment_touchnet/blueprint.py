# This file is part of the Indico plugins.
# Copyright (C) 2002 - 2022 CERN
#
# The Indico plugins are free software; you can redistribute
# them and/or modify them under the terms of the MIT License;
# see the LICENSE file for more details.

from indico.core.plugins import IndicoPluginBlueprint

from indico_payment_touchnet.controllers import RHTouchNetCancel, RHTouchNetIPN, RHTouchNetSuccess


blueprint = IndicoPluginBlueprint(
    'payment_touchnet', __name__,
    url_prefix='/event/<int:event_id>/registrations/<int:reg_form_id>/payment/response/touchnet'
)

blueprint.add_url_rule('/cancel', 'cancel', RHTouchNetCancel, methods=('GET', 'POST'))
blueprint.add_url_rule('/success', 'success', RHTouchNetSuccess, methods=('GET', 'POST'))
# Used by TouchNet to send an asynchronous notification for the transaction (pending, successful, etc)
blueprint.add_url_rule('/ipn', 'notify', RHTouchNetIPN, methods=('POST',))
