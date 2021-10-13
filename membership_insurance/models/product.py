# -*- coding: utf-8 -*-
##############################################################################
#
#    Odoo, Open Source Management Solution, third party addon
#    Copyright (C) 2004-2020 Vertel AB (<http://vertel.se>).
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

import base64
import datetime
import json
import logging
import re
import requests
import time

import dateutil
import dateutil.parser
import dateutil.relativedelta
import dateutil.rrule
import dateutil.tz
from odoo import models, fields, api, _
from odoo.tools.safe_eval import safe_eval
from odoo.addons import decimal_precision as dp
from odoo.exceptions import except_orm, UserError, RedirectWarning
from pytz import timezone


_logger = logging.getLogger(__name__)

class ProductTemplate(models.Model):
    _inherit = 'product.template'

    current_year = datetime.datetime.now().year
    insurance_product_ids = fields.Many2many(comodel_name='product.template', relation='insurance_product_rel', column1='product_id',column2='insurance_product_id', string='Invoice Products' ,domain="[('type', '=', 'service')]")

    # Python code
    insurance_code = fields.Text(string='Python Code', groups='base.group_system',
                       default= """# Available variables:
#  - env: Odoo Environment on which the action is triggered
#  - model: Odoo Model of the record on which the action is triggered; is a void recordset
#  - record: record on which the action is triggered; may be void
#  - records: recordset of all records on which the action is triggered in multi-mode; may be void
#  - time, datetime, dateutil, timezone: useful Python libraries
#  - log: log(message, level='info'): logging function to record debug information in ir.logging table
#  - Warning: Warning Exception to use with raise
#  - product; memberhsip product
#  - partner: partner to invoice
# To return an amount and qty, assign: \n
#        amount =  <something>
#        qty = <something>\n\n\n\n""",
                       help="Write Python code that holds advanced calcultations for amount and quantity")

    insurance = fields.Boolean(help='Check if the product is eligible for insurance.')
    insurance_date_from = fields.Date(string='Insurance Start Date',
                                      default=datetime.date(current_year, 4, 1 ),
                                      help='Date from which insurance becomes active.')
    insurance_date_to = fields.Date(string='Insurance End Date',
                                    default=datetime.date(current_year + 1, 3, 31),
                                    help='Date until which membership remains active.')

    _sql_constraints = [
        ('insurance_date_greater',
         'check(insurance_date_to >= insurance_date_from)',
         'Error! Ending Date cannot be set before Beginning Date.')
    ]

    @api.model
    def fields_view_get(self, view_id=None, view_type='form', toolbar=False, submenu=False):
        if self._context.get('product') == 'insurance_product':
            if view_type == 'form':
                view_id = self.env.ref('membership_insurance.insurance_products_form').id
            else:
                view_id = self.env.ref('membership_insurance.insurance_products_tree').id
        return super(ProductTemplate, self).fields_view_get(
            view_id=view_id, view_type=view_type, toolbar=toolbar, submenu=submenu)


class MembershipInsurance(models.TransientModel):
    _name = "membership.insurance"
    _description = "Insurance Credit Invoice"
    current_year = datetime.datetime.now().year
    membership_date_start = fields.Date(string="Membership Date Start",
                                        default=datetime.date(current_year, 4, 1))
    membership_date_end = fields.Date(string="Membership Date End",
                                      default=datetime.date(current_year + 1, 3, 31))

    product_id = fields.Many2one('product.product',
                                 string='Insurance Product',
                                 required=True)
    base_price = fields.Float(string='Base Price',
                              digits=dp.get_precision('Product Price'),
                              required=True)
    insurance_price = fields.Float(string='Total Insurance Price',
                                   compute='_compute_price',
                                   digits=dp.get_precision('Product Price'),
                                   readonly=True)
    total_days = fields.Integer(string="Total Insurance Days",
                                compute="_compute_days",
                                readonly=True)
    quantity = fields.Integer(string="Manual Quantity",
                              help="Keep at 0 to automatically calculate the amount of insuranses to invoice")


    @api.depends('membership_date_start', 'membership_date_end', 'base_price')
    def _compute_price(self):
        if not all((self.base_price, self.membership_date_start, self.membership_date_end)):
            return
        current_year = datetime.datetime.now().year
        line_obj = self.env['insurance.insurance_line']
        price_per_day = line_obj.price_per_day(None,
                                               price=self.base_price,
                                               date_from=datetime.date(current_year, 4, 1),
                                               date_to=datetime.date(current_year + 1, 3, 31))
        total_days = line_obj.days_between(self.membership_date_start,
                                           self.membership_date_end)
        if price_per_day and total_days:
            self.insurance_price = total_days * price_per_day

    @api.onchange('membership_date_start', 'membership_date_end')
    def _verify_days(self):
        line_obj = self.env['insurance.insurance_line']
        if not (self.membership_date_start and self.membership_date_end):
            return
        days = line_obj.days_between(self.membership_date_start,
                                     self.membership_date_end)
        if days < 30:
            return {
                'warning': {'title': _('Warning!'),
                            'message': _('Insurance has to be atleast 30 days.')}
            }
        if days > 360:
            return {
                'warning': {'title': _('Warning!'),
                            'message': _('Insurance period cannot be longer than 360 days..')}
            }

    @api.depends('membership_date_start', 'membership_date_end')
    def _compute_days(self):
        line_obj = self.env['insurance.insurance_line']
        self.total_days = line_obj.days_between(self.membership_date_start, self.membership_date_end)


    @api.onchange('product_id')
    def onchange_product(self):
        """
        This function returns value of product's member price based on product id.
        """
        price_dict = self.product_id.price_compute('list_price')
        self.base_price = price_dict.get(self.product_id.id) or False

    @api.multi
    def membership_insurance(self):
        datas = {
            'insurance_product_id': self.product_id.id,
            'amount': self.insurance_price
        }
        invoice_list = self.env['res.partner'].browse(self._context.get('active_ids')).create_insurance_invoice(datas=datas, manual_quantity = self.quantity)

        for invoice in invoice_list:
            for line in invoice.invoice_line_ids:
                self.env['insurance.insurance_line'].create({'partner': invoice.partner_id.id,
                                                             'date_from': self.membership_date_start,
                                                             'date_to': self.membership_date_end,
                                                             'insurance_id': line.product_id.id,
                                                             'insurance_price': line.price_unit * line.quantity,
                                                             'original_insurance_price': line.price_unit * line.quantity,
                                                             'account_invoice_line': line.id,
                                                             'original_quantity': line.quantity,
                                                             'quantity': line.quantity})

        search_view_ref = self.env.ref('account.view_account_invoice_filter', False)
        form_view_ref = self.env.ref('account.invoice_form', False)
        tree_view_ref = self.env.ref('account.invoice_tree', False)

        return {
            'domain': [('id', 'in', [invoice.id for invoice in invoice_list])],
            'name': 'Insurance Invoices',
            'res_model': 'account.invoice',
            'type': 'ir.actions.act_window',
            'views': [(tree_view_ref.id, 'tree'), (form_view_ref.id, 'form')],
            'search_view_id': search_view_ref and search_view_ref.id,
        }


class ProductProduct(models.Model):
    _inherit = 'product.product'

    @api.multi
    def insurance_get_amount_qty(self, partner, manual_quantity = None):
        eval_context = {
            'uid': self._uid,
            'user': self.env.user,
            'time': time,
            'datetime': datetime,
            'dateutil': dateutil,
            'timezone': timezone,
            'b64encode': base64.b64encode,
            'b64decode': base64.b64decode,
            'partner': partner,
            'product': self,
        }
        safe_eval(self.insurance_code.strip(), eval_context, mode="exec", nocopy=True)  # nocopy allows to return 'action'
        return (eval_context.get('amount', False), eval_context.get('qty', False))


class AccountInvoiceLine(models.Model):
    _inherit = "account.invoice.line"
    # ~ total_days = fields.Integer(related="invoice_id.total_days")
    # ~ price_unit = fields.Float(compute='_get_price_on_days')
    # ~ price_subtotal =fields.Float(compute='_get_price_on_days')
    def _get_invoice_line_name_from_product(self):
        """ Returns the automatic name to give to the invoice line depending on
        the product it is linked to.
        """
        self.ensure_one()
        if not self.product_id:
            return ''
        return self.product_id.name

