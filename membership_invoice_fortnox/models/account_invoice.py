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

    is_fortnox = fields.Boolean('Fortnox', default=True)
    
    # ~ invoice_ids = fields.Many2many('account.invoice', 'account_invoice_account_invoice_send_rel', string='Invoices')
    
    
    @api.multi
    def send_and_print_action(self):
        res = super(AccountInvoiceSend, self).send_and_print_action()
        if self.is_fortnox:
            for invoice in self.invoice_ids:
                invoice.fortnox_create()
        return res

class account_invoice(models.Model):
    _inherit = 'account.invoice'
    
    @api.multi
    def fortnox_create(self):
        # Customer (POST https://api.fortnox.se/3/customers)
        for invoice in self:
            if not invoice.date_due:
                raise Warning("Please select payment term")
            if not invoice.partner_id.commercial_partner_id.ref:
                # ~ raise Warning("You have not updated this customer to the fortnox list.")
                # ~ ref = invoice.partner_id.commercial_partner_id.fortnox_update()
                ref = invoice.partner_id.fortnox_update()
            InvoiceRows = []
            for line in invoice.invoice_line_ids:
                InvoiceRows.append(
                        {
                            "AccountNumber": line.account_id.code,
                            "DeliveredQuantity": line.quantity,
                            "Description": line.name,
                            "Price":line.price_unit,
                            # ~ "Unit": "st",
                            "VAT": int(line.invoice_line_tax_ids.mapped('amount')[0]),
                        })
            r = self.env['res.config.settings'].fortnox_request('post',"https://api.fortnox.se/3/invoices",
                data={                   
                "Invoice": {
                    "Comments": "",
                    # ~ "Credit": "false",
                    "CreditInvoiceReference": 0,
                    "Currency": "SEK",
                    "CustomerName": invoice.partner_id.commercial_partner_id.name,
                    "CustomerNumber": invoice.partner_id.commercial_partner_id.ref,
                    "DueDate":invoice.date_due.strftime('%Y-%m-%d'),
                    "InvoiceDate": invoice.date_invoice.strftime('%Y-%m-%d'),
                    "InvoiceRows": InvoiceRows,
                    "InvoiceType": "INVOICE",
                    "Language": "SV",
                    # ~ "Net": 1590,
                    "Remarks": "",
                    # ~ "Sent": false,
                    "TermsOfPayment": "30",
                    # ~ "Total": 1988,
                    # ~ "TotalToPay": 1988,
                    # ~ "TotalVAT": 397.5,
                }
            })
            
            r = json.loads(r)
            # ~ if not r["Invoice"]["CustomerNumber"]:
            # ~ raise Warning(str(r))
            invoice.ref = r["Invoice"]["CustomerNumber"]
            return r
            
