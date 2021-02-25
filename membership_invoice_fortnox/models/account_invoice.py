# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models
from odoo.exceptions import Warning
import warnings
import time

from datetime import datetime
import requests
import json

import logging
_logger = logging.getLogger(__name__)

class AccountInvoice(models.Model):
    _inherit = "account.invoice"
    
    def remove_free_lines(self):
        """ SFM does not want package products to show on the invoice. Call this function to remove them.
        """
        #_logger.warn("~ Got invoice %s with %s lines!" % (self.id, len(self.invoice_line_ids)))
        self.state = 'draft'
        for line in self.invoice_line_ids:
            #_logger.warn("~ the line named %s has %s products" % (line.display_name, len(line.product_id.membership_product_ids)))
            if len(line.product_id.membership_product_ids) > 0:
                #_logger.warn("~ removing %s with id %s from invoice" % (line.display_name, line.id))
                line.unlink()
        self.state = 'open'

class AccountInvoiceSend(models.TransientModel):
    _inherit = 'account.invoice.send'

    is_fortnox = fields.Boolean(string='Fortnox',default=True)
    
    @api.multi
    def send_and_print_action(self):
        res = super(AccountInvoiceSend, self).send_and_print_action()
        if self.is_fortnox:
            for invoice in self.invoice_ids:
                time.sleep(1)
                if not invoice.name:
                    invoice.remove_free_lines()
                    invoice.fortnox_create()
        return res

