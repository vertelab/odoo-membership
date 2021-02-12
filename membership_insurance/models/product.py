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

from odoo import models, fields, api, _
import time
from datetime import datetime
from odoo.tools.safe_eval import safe_eval
from pytz import timezone
from odoo.addons import decimal_precision as dp
import re
from odoo.exceptions import except_orm, Warning, RedirectWarning
import requests
import json
import logging
import dateutil
import dateutil.parser
import dateutil.relativedelta
import dateutil.rrule
import dateutil.tz
import base64
_logger = logging.getLogger(__name__)

class ProductTemplate(models.Model):
    _inherit = 'product.template'
    
    current_year = datetime.now().year
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
#        amount =  <somethin>
#        qty = <something>\n\n\n\n""",
                       help="Write Python code that holds advanced calcultations for amount and quatity")
    insurance = fields.Boolean(help='Check if the product is eligible for insurance.')
    insurance_date_from = fields.Date(string='Insurance Start Date', default=datetime.now().strftime('%Y-04-01'),
        help='Date from which insurance becomes active.')
    insurance_date_to = fields.Date(string='Insurance End Date', default=datetime.now().strftime('%s-03-31' %(current_year + 1)),
        help='Date until which membership remains active.')

    _sql_constraints = [
        ('insurance_date_greater', 'check(insurance_date_to >= insurance_date_from)', 'Error ! Ending Date cannot be set before Beginning Date.')
    ]

    @api.model
    def fields_view_get(self, view_id=None, view_type='form', toolbar=False, submenu=False):
        if self._context.get('product') == 'insurance_product':
            if view_type == 'form':
                view_id = self.env.ref('membership_insurance.insurance_products_form').id
            else:
                view_id = self.env.ref('membership_insurance.insurance_products_tree').id
        return super(ProductTemplate, self).fields_view_get(view_id=view_id, view_type=view_type, toolbar=toolbar, submenu=submenu)

class MembershipInsurance(models.TransientModel):
    _name = "membership.insurance"
    _description = "Insurance Credit Invoice"
    # ~ current_year = datetime.now().year
    # ~ membership_date_start = fields.Date(string = "Membership Date Start",default=datetime.now().strftime('%Y-04-01'))
    # ~ membership_date_end = fields.Date(string = "Membership Date End",default=datetime.now().strftime('%s-03-31' %(current_year + 1)) )

    product_id = fields.Many2one('product.product', string='Insurance Product', required=True)
    insurance_price = fields.Float(string='Insurance Price', digits= dp.get_precision('Product Price'), required=True)
    
    # ~ total_days = fields.Integer(string = "Total Insurance Days", compute='_get_insurance_credit_days', readonly=True)
    
    # ~ @api.multi
    # ~ @api.onchange('invoice.partner_id.date_start','invoice.partner_id.date_end')
    # ~ def _get_insurance_credit_days(self):
        # ~ for partner in self.env['res.partner'].browse(self._context.get('active_ids')):
            # ~ if partner.date_start:
                # ~ if partner.date_start > self.membership_date_start:
                    # ~ invoice.total_days = ((invoice.membership_date_end - invoice.partner_id.date_start).days + 1) /365 * 360 
                    # ~ if invoice.total_days >= 360:
                        # ~ raise Warning('It is longer than one year, please doubble check the joint date for client %s ' %invoice.partner_id.name)
            # ~ if partner.date_end:
                # ~ if partner.date_end < self.membership_date_end:
                    # ~ self.total_days = ((self.membership_date_end - parnter.date_end).days + 1) /365 * 360 - 30
                    # ~ if self.total_days < 30:
                        # ~ raise Warning('Days left is less than 30 days, you do not need to create credit invoice for client %s ' %invoice.partner_id.name)

    @api.onchange('product_id')
    def onchange_product(self):
        """This function returns value of  product's member price based on product id.
        """
        price_dict = self.product_id.price_compute('list_price')
        self.insurance_price = price_dict.get(self.product_id.id) or False

    @api.multi
    def membership_insurance(self):
        if self:
            datas = {
                'insurance_product_id': self.product_id.id,
                'amount': self.insurance_price
            }
        invoice_list = self.env['res.partner'].browse(self._context.get('active_ids')).create_insurance_invoice(datas=datas)

        search_view_ref = self.env.ref('account.view_account_invoice_filter', False)
        form_view_ref = self.env.ref('account.invoice_form', False)
        tree_view_ref = self.env.ref('account.invoice_tree', False)

        return  {
            'domain': [('id', 'in', invoice_list)],
            'name': 'Insurance Invoices',
            'res_model': 'account.invoice',
            'type': 'ir.actions.act_window',
            'views': [(tree_view_ref.id, 'tree'), (form_view_ref.id, 'form')],
            'search_view_id': search_view_ref and search_view_ref.id,
        }

class ProductProduct(models.Model):
    _inherit = 'product.product'

    @api.multi
    def insurance_get_amount_qty(self, partner):
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
        safe_eval(self.membership_code.strip(), eval_context, mode="exec", nocopy=True)  # nocopy allows to return 'action'
        return (eval_context.get('amount',self.list_price),eval_context.get('qty',1.0))


        
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
        
    # ~ @api.multi
    # ~ @api.onchange('invoice_id.price_unit','inovice_id.price_subtotal')
    # ~ def _get_price_on_days(self):
        # ~ if self.commercial_partner_id.date_start or self.commercial_partner_id.date_end
        # ~ for invoice_line in self:
            # ~ if invoice_line.total_days != 0:
                # ~ for line in self:
                    # ~ line.price_unit = line.product_id.lst_price / 360 * invoice_line.total_days
                    # ~ line.price_subtotal = line.price_unit * line.quantity
            
            # ~ else:
                # ~ for line in self:
                    # ~ line.price_unit = line.product_id.lst_price 
                    # ~ line.price_subtotal = line.price_unit * line.quantity
            
            
        
        
# ~ class AccountInvoice(models.Model):
    # ~ _inherit = "account.invoice"
    # ~ current_year = datetime.now().year
    # ~ membership_date_start = fields.Date(string = "Membership Date Start",default=datetime.now().strftime('%Y-04-01'))
    # ~ membership_date_end = fields.Date(string = "Membership Date End",default=datetime.now().strftime('%s-03-31' %(current_year + 1)) )
    # ~ total_days = fields.Integer(string = "Total Mebership Days", compute='_get_membership_days', readonly=True)

    
    
    # ~ @api.multi
    # ~ @api.onchange('invoice.partner_id.date_start','invoice.partner_id.date_end')
    # ~ def _get_membership_days(self):
        # ~ for invoice in self:
            # ~ if invoice.partner_id.date_start:
                # ~ if invoice.partner_id.date_start > invoice.membership_date_start:
                    # ~ invoice.total_days = ((invoice.membership_date_end - invoice.partner_id.date_start).days + 1) /365 * 360 
                    # ~ if invoice.total_days >= 360:
                        # ~ raise Warning('It is longer than one year, please doubble check the joint date for client %s ' %invoice.partner_id.name)
            # ~ elif invoice.partner_id.date_end:
                # ~ if invoice.partner_id.date_end < invoice.membership_date_end:
                    # ~ invoice.total_days = ((invoice.membership_date_end - invoice.partner_id.date_end).days + 1) /365 * 360 - 30
                    # ~ if invoice.total_days < 30:
                        # ~ raise Warning('Days left is less than 30 days, you do not need to create credit invoice for client %s ' %invoice.partner_id.name)
                
    

