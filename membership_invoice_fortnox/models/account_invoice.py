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

BASE_URL = 'https://api.fortnox.se'

class AccountInvoice(models.Model):
    _inherit = "account.invoice"

    def remove_zero_cost_lines(self):
        """
        SFM does not want products with 0 cost to show on the invoice.
        Call this function to remove them.
        """
        self.state = 'draft'
        for line in self.invoice_line_ids:
            if line.price_unit == 0 and line.quantity == 0:
                line.unlink()
        self.state = 'open'

    def remove_package_products(self):
        """
        SFM does not want package products to show on the invoice.
        Call this function to remove them.
        This function is replaced remove_zero_cost_lines()
        """
        self.state = 'draft'
        for line in self.invoice_line_ids:
            if len(line.product_id.membership_product_ids) > 0 and line.price_unit == 0 and line.quantity == 0:
                line.unlink()
        self.state = 'open'

class AccountInvoiceSend(models.TransientModel):
    _inherit = 'account.invoice.send'
    is_fortnox = fields.Boolean(string='Fortnox', default=True)

    @api.multi
    def send_and_print_action(self):
        """
        Override normal send_and_print_action with additional
        functionality for fortnox.
        """
        res = super(AccountInvoiceSend, self).send_and_print_action()
        if self.is_fortnox:
            for invoice in self.invoice_ids:
                time.sleep(1)
                if not invoice.name:
                    invoice.remove_zero_cost_lines()
                    invoice.fortnox_create()
        return res

    def update_invoice_status_fortnox_cron(self):
        """Update invoice status from fortnox."""
        states = {'cancelled': 'cancel',
                  'fullypaid': 'paid',
                  'unpaid': 'open',
                  'unpaidoverdue': 'open'}
        for state in states:
            # Only care for the fullypaid at the moment, may be extended
            # in the future.
            if not state == 'fullypaid':
                continue
            r = self.company_id.fortnox_request(
                'get',
                f'{BASE_URL}/3/invoices/?filter={state}')
            r = r.json.loads(r)
            if r.get('ErrorInformation'):
                _logger.error(f'Failed to get the state: {state} from fortnox')
            else:
                for inv in r.get('Invoices', []):
                    name = inv.get("DocumentNumber")
                    invoice = self.env['account.invoice'].search(['name', '=', name])
                    if invoice:
                        invoice.state = states[state]
