# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models
from odoo.exceptions import Warning
import warnings

from datetime import datetime
import requests
import json

import logging
_logger = logging.getLogger(__name__)



class AccountInvoiceSend(models.TransientModel):
    _inherit = 'account.invoice.send'

    is_fortnox = fields.Boolean(string='Fortnox',default=True)
    
    
    @api.multi
    def send_and_print_action(self):
        res = super(AccountInvoiceSend, self).send_and_print_action()
        if self.is_fortnox:
            for invoice in self.invoice_ids:
                # ~ raise Warning(invoice)
                invoice.fortnox_create()
        return res


    
    
