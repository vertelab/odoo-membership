# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models
from odoo.exceptions import Warning
from odoo.tools.safe_eval import safe_eval

import datetime
import time

from pytz import timezone
import logging
_logger = logging.getLogger(__name__)

# build dateutil helper, starting with the relevant *lazy* imports
import dateutil
import dateutil.parser
import dateutil.relativedelta
import dateutil.rrule
import dateutil.tz
import base64
import requests
import json
class ProductTemplate(models.Model):
    _inherit = 'product.template'

    membership_product_ids = fields.Many2many(comodel_name='product.template', relation='membership_product_rel', column1='product_id',column2='member_product_id', string='Membership Products' ,domain="[('membership','=',True), ('type', '=', 'service')]")
   
    # Python code
    membership_code = fields.Text(string='Python Code', groups='base.group_system',
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



class ProductProduct(models.Model):
    _inherit = 'product.product'
    
    # ~ company_id = fields.Many2one(
    # ~ 'res.company',
    # ~ 'Company',
    # ~ default=lambda self: self.env.user.company_id 
    # ~ )
    
    @api.multi
    def membership_get_amount_qty(self, partner):
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

    @api.multi
    def article_update(self):
        for product in self:
            if not product.default_code:
                raise Warning('You do not have set default code yet.')
            if product.default_code:
                try:
                    url = "https://api.fortnox.se/3/articles/%s" % product.default_code
                    #r = response
                    r = self.env.user.company_id.fortnox_request('put',url,
                        data={
                            "Article": 
                                    {
                                        "Description": product.name,
                                        # ~ "ArticleNumber": product.default_code,
                                        # ~ "SalesPrice": product.lst_price,
                                    }
                        })
                    
                except requests.exceptions.RequestException as e:
                    _logger.warn('%s' %e)
                    # ~ product.default_code = r["Article"]["ArticleNumber"]
                    
                url = "https://api.fortnox.se/3/articles"
                """ r = response """
                r = self.env.user.company_id.fortnox_request('post', url,
                    data={
                        "Article": 
                                {
                                    "Description": product.name,
                                    "ArticleNumber": product.default_code,
                                    # ~ "SalesPrice": product.lst_price,
                                }
                    })
                    # ~ _logger.warn('%s Haze company_id' % self.env.user.company_id )
                r = json.loads(r)
                
            
            # ~ raise Warning('%s Haze' %str(r))
            # ~ _logger.warn('%s Haze code' %product.default_code)
            return r  

    """This is for Omsättning product, It changes every year, but with this code it will be easier to paste in omsättnings product"""
    # ~ amount =  0.0
    # ~ if partner.revenue > 10000000 and partner.revenue <= 50000000:
        # ~ amount = 5000.0
    # ~ elif partner.revenue > 50000000 and partner.revenue <= 100000000:
        # ~ amount = 10000.0
    # ~ elif partner.revenue > 100000000 and partner.revenue <= 200000000:
        # ~ amount = 20000.0
    # ~ elif partner.revenue > 200000000 and partner.revenue <= 300000000:
        # ~ amount = 30000.0
    # ~ elif partner.revenue > 300000000 and partner.revenue <= 400000000:
        # ~ amount = 40000.0
    # ~ elif partner.revenue > 400000000 and partner.revenue <= 500000000:
        # ~ amount = 50000.0
    # ~ elif partner.revenue > 500000000 and partner.revenue <= 600000000:
        # ~ amount = 60000.0
    # ~ elif partner.revenue > 600000000 and partner.revenue <= 700000000:
        # ~ amount = 70000.0
    # ~ elif partner.revenue > 700000000 and partner.revenue <= 800000000:
        # ~ amount = 80000.0
    # ~ elif partner.revenue > 800000000 and partner.revenue <= 900000000:
        # ~ amount = 90000.0
    # ~ elif partner.revenue > 900000000 and partner.revenue <= 1000000000:
        # ~ amount = 100000.0
    # ~ elif partner.revenue > 1000000000:
        # ~ amount = 100000.0


class res_partner(models.Model):
    _inherit="res.partner"
       
    @api.multi
    def create_membership_invoice(self, product_id=None, datas=None):
        """ Create Customer Invoice of Membership for partners.
        @param datas: datas has dictionary value which consist Id of Membership product and Cost Amount of Membership.
                      datas = {'membership_product_id': None, 'amount': None}
        """
        # ~ raise Warning(product_id,datas)
        invoice_list = super(res_partner,self).create_membership_invoice(product_id=product_id,datas=datas)
        # Add extra products
        for invoice in self.env['account.invoice'].browse(invoice_list):
            for line in invoice.invoice_line_ids:
                for member_product in line.product_id.membership_product_ids:
                    # create a record in cache, apply onchange then revert back to a dictionnary
                    invoice_line = self.env['account.invoice.line'].new({'product_id': member_product.id,'price_unit': member_product.lst_price,'inovice_id':invoice.id})
                    invoice_line._onchange_product_id()
                    line_values = invoice_line._convert_to_write({name: invoice_line[name] for name in invoice_line._cache})
                    line_values['name'] = member_product.name
                    line_values['account_id'] = member_product.property_account_income_id.id if member_product.property_account_income_id else self.env['account.account'].search([('user_type_id','=',self.env.ref('account.data_account_type_revenue').id)])[0].id 
                    invoice.write({'invoice_line_ids': [(0, 0, line_values)]})
        # Calculate amount and qty
        for invoice in self.env['account.invoice'].browse(invoice_list):
            for line in invoice.invoice_line_ids:
                if line.product_id.membership_code:
                    line.price_unit,line.quantity = line.product_id.membership_get_amount_qty(invoice.partner_id)
        return invoice_list
