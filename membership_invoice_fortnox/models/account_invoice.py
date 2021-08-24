# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from datetime import datetime, timedelta
import logging
import json
import time

from odoo import api, fields, models
from odoo.exceptions import Warning

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

    def update_invoice_status_fortnox_cron(self):
        """Update invoice status from fortnox."""

        # Assumption that most invoices are paid rather than canceled.
        # Python conserves dict order since Python 3.7 so order matters.
        states = {'fullypaid': 'paid',
                  'cancelled': 'cancel',}

        # States we don't care about.
        #          'unpaid': 'open',
        #          'unpaidoverdue': 'open'}

        # Cutof date to not check too old invoices.
        from_date = datetime.now() - timedelta(days=365)
        # Allow for multi company.
        for company in self.env['res.company'].search([]):
            for invoice in self.env['account.invoice'].search(
                    [('company_id', '=', company.id),
                     ('create_date', '>', from_date)]):
                for state in states:
                    # Only allowed to do 4 requests per second to Fortnox.
                    # Do 3 requests per second just to be sure.
                    time.sleep(0.3)
                    try:
                        r = company.fortnox_request(
                            'get',
                            f'{BASE_URL}/3/invoices/?filter={state}&documentnumber={invoice.name}&fromdate={from_date.strftime("%Y-%m-%d")}')
                        r = json.loads(r)
                    except:
                        _logger.error(f'Could not find invoice with name: {invoice.name}')
                        _logger.error(r.get('ErrorInformation'))
                        continue
                    for inv in r.get('Invoices', []):
                        if invoice.name == inv.get('DocumentNumber'):
                            _logger.info(f'{invoice.name}: {state}')
                            _logger.debug(str(invoice.read()))
                            invoice.state = states[state]
                            break
                    else:
                        # If we found an invoice we do not have to check
                        # next state.
                        break


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
