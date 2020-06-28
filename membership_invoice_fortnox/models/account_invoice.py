# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models
from odoo.exceptions import Warning

import requests
import json

import logging
_logger = logging.getLogger(__name__)



class account_invice(models.Model):
    _inherit = 'account.invoice'
    
    @api.multi
    def fortnox_create(self):
        # Customer (POST https://api.fortnox.se/3/customers)
        for invoice in self:
            if not invoice.partner_id.commercial_partner_id.ref:
                InvoiceRows = [
                            {
                                "AccountNumber": 3011,
                                "DeliveredQuantity": "10.00",
                                "Description": "USB-minne 32GB",
                                "Price": 159,
                                "Total": 1590,
                                "Unit": "st",
                                "VAT": 25
                            }
                        ]
                r = self.env['res.config.settings'].fortnox_request('post',"https://api.fortnox.se/3/invoices",
                    data={                   
                    "Invoice": {
                        "Comments": "",
                        "Credit": "false",
                        "CreditInvoiceReference": 0,
                        "Currency": "SEK",
                        "CustomerName": invoice.partner_id.commersial_partner_id.name,
                        "CustomerNumber": invoice.partner_id.commersial_partner_id.ref,
                        "DueDate": "2015-02-11",
                        "InvoiceDate": "2015-01-12",
                        "InvoiceRows": InvoiceRows,
                        "InvoiceType": "INVOICE",
                        "Language": "SV",
                        "Net": 1590,
                        "Remarks": "",
                        # ~ "Sent": false,
                        "TermsOfPayment": "30",
                        "Total": 1988,
                        "TotalToPay": 1988,
                        "TotalVAT": 397.5,
                    }
                })
 
                invoice.ref = r.content.get('DocumentNumber')
                return r
            