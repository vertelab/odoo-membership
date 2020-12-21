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
import re
from odoo.exceptions import except_orm, Warning, RedirectWarning
import requests
import json
import logging
from . import insurance
_logger = logging.getLogger(__name__)


class insurance_permission(models.Model):
    _name = 'insurance.permission'
    
    name = fields.Char(string="Name")
    
class insurance_license(models.Model):
    _name = 'insurance.license'
    
    name = fields.Char(string="Name")
    
class insurance_role(models.Model):
    _name = 'insurance.role'
    
    name = fields.Char(string="Role")

class MembershipLine(models.Model):
    _inherit="membership.membership_line"
    quantity = fields.Float(string="Quantity", related="account_invoice_line.quantity",readonly="1")
    
class res_partner(models.Model):
    _inherit = 'res.partner'
    

    liability_insurance = fields.Many2many(comodel_name='insurance.license', string='Insurance License')
    liability_insurance_permission = fields.Many2many(comodel_name='insurance.permission', string='Insurance Permission')
    company_role = fields.Many2one(comodel_name='insurance.role',string='Role') 
    internal_notes = fields.Text(string='Internal notes')
    date_start = fields.Date(string = "Date Start")
    date_end = fields.Date(string = "Date End")
    


    @api.one
    def _compute_count_company(self):
        
        
        if self.insurance_company_type == 'fellowship':
            self.count_company                      = self.env['res.partner'].search_count([('id', 'child_of', self.id),('insurance_company_type', '=', 'company')])
            self.count_co_life_permission           = self.env['res.partner'].search_count([('id', 'child_of', self.id),('insurance_company_type', '=', 'company'),('liability_insurance_permission', '=', self.env.ref('membership_insurance.crm_insurance_life_permission').id)])
            self.count_co_property_permission       = self.env['res.partner'].search_count([('id', 'child_of', self.id),('insurance_company_type', '=', 'company'),('liability_insurance_permission', '=', self.env.ref('membership_insurance.crm_insurance_property_permission').id)])
            self.count_co_property_life_permission  = self.env['res.partner'].search_count([('id', 'child_of', self.id),('insurance_company_type', '=', 'company'),('liability_insurance_permission', '=', self.env.ref('membership_insurance.crm_insurance_property_permission').id),('liability_insurance_permission', '=', self.env.ref('membership_insurance.crm_insurance_life_permission').id)])


        if self.insurance_company_type in ['fellowship','company']:
    
            self.count_ac_life_licence = self.env['res.partner'].search_count([('id', 'child_of', self.id),('insurance_company_type', '=', 'accommodator'),('liability_insurance', '=', self.env.ref('membership_insurance.crm_insurance_life_permission').id)])
            self.count_ac_property_licence = self.env['res.partner'].search_count([('id', 'child_of', self.id),('insurance_company_type', '=', 'accommodator'),('liability_insurance', '=', self.env.ref('membership_insurance.crm_insurance_property_permission').id)])
            self.count_ac_property_life_licence = self.env['res.partner'].search_count([('id', 'child_of', self.id),('insurance_company_type', '=', 'accommodator'),('liability_insurance', '=', self.env.ref('membership_insurance.crm_insurance_property_permission').id),('liability_insurance', '=', self.env.ref('membership_insurance.crm_insurance_life_permission').id)])

            self.count_accommodator         = self.env['res.partner'].search_count([('id', 'child_of', self.id),('insurance_company_type', '=', 'accommodator')])

            self.count_ac_life = self.env['res.partner'].search_count([('id', 'child_of', self.id),('liability_insurance', '=', self.env.ref('membership_insurance.crm_insurance_life').id)])
            self.count_ac_property = self.env['res.partner'].search_count([('id', 'child_of', self.id),('liability_insurance', '=', self.env.ref('membership_insurance.crm_insurance_property').id)])
            self.count_ac_property_life = self.env['res.partner'].search_count([('id', 'child_of', self.id),('liability_insurance', '=', self.env.ref('membership_insurance.crm_insurance_property').id),('liability_insurance', '=', self.env.ref('membership_insurance.crm_insurance_life').id)])
    
    count_company               = fields.Integer(string='Company', compute ='_compute_count_company')
    count_co_life_permission    = fields.Integer(string='Company Life Permission', compute ='_compute_count_company')
    count_co_property_permission    = fields.Integer(string='Company Property Permission', compute ='_compute_count_company')
    count_co_property_life_permission    = fields.Integer(string='Company Property/Life Permission', compute ='_compute_count_company')

    count_ac_life_licence    = fields.Integer(string='Accommodator Life Licence', compute ='_compute_count_company')
    count_ac_property_licence    = fields.Integer(string='Accommodator Property Licence', compute ='_compute_count_company')
    count_ac_property_life_licence    = fields.Integer(string='Accommodator Property/Life Licence', compute ='_compute_count_company')

    count_accommodator   = fields.Integer(string='Accommodators', compute ='_compute_count_company')
    count_ac_life        = fields.Integer(string='Accommodator Life', compute ='_compute_count_company')
    count_ac_property    = fields.Integer(string='Accommodator Property', compute ='_compute_count_company')
    count_ac_property_life    = fields.Integer(string='Accommodator Property/Life', compute ='_compute_count_company')
    
    vat = fields.Char(string='Tax ID', help="The Tax Identification Number. Complete it if the contact is subjected to government taxes. Used in some legal statements.")
    personnumber = fields.Char(string='Person Number',help="This is person number")

    
    def _fellowship(self):
        for partner in self:
            if partner.insurance_company_type in ['accommodator','company']:
                if partner.insurance_company_type == 'company':
                    partner.fellowship_id = partner.parent_id
                elif partner.insurance_company_type == 'accommodator':
                    partner.fellowship_id = partner.parent_id.parent_id
                    partner.insurance_company_id = partner.parent_id
   
            
    fellowship_id =  fields.Many2one(comodel_name='res.partner', compute = '_fellowship') 
    insurance_company_id = fields.Many2one(comodel_name='res.partner', compute = '_fellowship') 
    
    
    def _compute_gender(self):
        self.count_man = self.env['res.partner'].search_count([('id', 'child_of', self.id),('gender', '=', 'man')])
        self.count_woman = self.env['res.partner'].search_count([('id', 'child_of', self.id),('gender', '=', 'woman')])
    gender = fields.Selection([('man', 'Male'), ('woman', 'Female')])
    
    count_man = fields.Integer(String='Male', compute = '_compute_gender')
    count_woman = fields.Integer(String='Female', compute = '_compute_gender')
    
    
    @api.one
    def _compute_org_prn(self):
        if self.company_type == 'company':
            self.org_prn = self.company_registry
            
        elif self.company_type == 'person':
            self.org_prn = self.personnumber
            
    org_prn = fields.Char(string="Org/pers-nummer", compute ='_compute_org_prn')
    
    @api.onchange('insurance_company_type')
    def onchange_insurance_company_type(self):
        self.is_company = (self.insurance_company_type not in ['person','accommodator'])
        self.company_type = 'company' if self.is_company else 'person'
    def _insurance_write_company_type(self):
        for partner in self:
            partner.is_company = (partner.insurance_company_type not in ['person','accommodator'])
            partner.company_type = 'company' if partner.is_company else 'person'
    insurance_company_type = fields.Selection(string='Company Type',
        selection=[('person', 'Individual'),('fellowship', 'Fellowship'),('company', 'Company'),('accommodator', 'Accommodator')],
        inverse='_insurance_write_company_type')
    revenue = fields.Integer(string='Revenue',help="Revenue in tkr")
    revenue_property = fields.Integer(string='Revenue Propery')
    revenue_life = fields.Integer(string='Revenue Life')

    @api.multi
    def _action_button(self,domain):
        partner_ids = self.ids
        partner_ids.append(self.env.user.partner_id.id)
        action = self.env['ir.actions.act_window'].for_xml_id('contacts', 'action_contacts')
        action['context'] = {
            'default_partner_ids': partner_ids,
        }
        action['domain'] = domain
        return action
        
    @api.multi
    def company_button(self):
        return self._action_button([('id', 'child_of', self.id),('insurance_company_type', '=', 'company')])

    @api.multi
    def fellowship_button(self):
        return self._action_button([('id', 'child_of', self.id),('insurance_company_type', '=', 'fellowship')])

    @api.multi
    def accommodator_button(self):
        return self._action_button([('id', 'child_of', self.id),('insurance_company_type', '=', 'accommodator')])
    
    @api.multi
    def life_insurance_button(self):
        return self._action_button([('id', 'child_of', self.id),('liability_insurance', '=', self.env.ref('membership_insurance.crm_insurance_life').id)])

    @api.multi
    def property_insurance_button(self):
        return self._action_button([('id', 'child_of', self.id),('liability_insurance', '=', self.env.ref('membership_insurance.crm_insurance_property').id)])

    @api.multi
    def life_protperty_insurance_button(self):
        return self._action_button([('id', 'child_of', self.id),('liability_insurance', '=', self.env.ref('membership_insurance.crm_insurance_life').id),('liability_insurance', '=', self.env.ref('membership_insurance.crm_insurance_property').id)])
        
    @api.multi
    def life_permission_button(self):
        return self._action_button([('id', 'child_of', self.id),('liability_insurance_permission', '=', self.env.ref('membership_insurance.crm_insurance_life_permission').id)])
        
    @api.multi
    def property_permission_button(self):
        return self._action_button([('id', 'child_of', self.id),('liability_insurance_permission', '=', self.env.ref('membership_insurance.crm_insurance_property_permission').id)])
        
    @api.multi
    def life_protperty_permission_button(self):
        return self._action_button([('id', 'child_of', self.id),('liability_insurance_permission', '=', self.env.ref('membership_insurance.crm_insurance_life_permission').id),('liability_insurance_permission', '=', self.env.ref('membership_insurance.crm_insurance_property_permission').id)])
    
    
    def onchange_parent_id(self):
        
        return {}
        
    
    def _fields_sync(self, values):
        """ Sync commercial fields and address fields from company and to children after create/update,
        just as if those were all modeled as fields.related to the parent """
        return 
        
    def merge_comment(self):
        for contact in self.env['res.partner'].search([]):
            _logger.warn(('%s test test ' ) %contact.comment)
            if not contact.internal_notes and contact.comment:
                
                contact.internal_notes = contact.comment 
                
    def set_payment_term(self):
        for partner in self.env['res.partner'].search([('property_payment_term_id','=',False)]):
          partner.property_payment_term_id = self.env['account.payment.term'].search([('id','=',3)])
    
    def delete_free_membership(self):
        for partner in self.env['res.partner'].search([]):
            partner.free_member = False
            
    def find_bug(self):
        bugs = self.env['res.partner'].search([('city','=',False)])
        for partner in bugs:
            _logger.warn('%s Haze name' %partner.name)
            if partner.parent_id:
                partner.zip = partner.parent_id.zip
                partner.city = partner.parent_id.city
                
            
        # ~ raise Warning(bugs)
        
    def set_associate_member(self):
        for partner in self.env['res.partner'].search([]):
            partner.associate_member = partner.parent_id
        
    """ This is code for finding contacts which has no city or email in the database, it is for serveraction because it is not working in the pyton which is strange :(
    bugs = env['res.partner'].search(['|',('email','=',False),('city','=',False)])
    res = env['ir.actions.act_window'].for_xml_id(
    'membership', 'action_membership_members')
    res['domain'] = "[('id','in',%s)]" % bugs.mapped('id')
    action = res"""
            
    # for insurance page
    associate_member = fields.Many2one('res.partner', string='Associate Member',
        help="A member with whom you want to associate your insurance."
             "It will consider the insurance state of the associated member.")
             
    insurance_lines = fields.One2many('insurance.insurance_line', 'partner', string='Insurance')
    
    insurance_amount = fields.Float(string='Insurance Amount', digits=(16, 2),
        help='The price negotiated by the partner')
    insurance_state = fields.Selection(insurance.STATE, compute='_compute_insurance_state',
        string='Current Insurance Status', store=True,
        help='It indicates the insurance state.\n'
             '-Non insurance: A partner who has not applied for any insurance.\n'
             '-Cancelled insurance: A insurance who has cancelled his insurance.\n'
             '-Old insurance: A insurance whose insurance date has expired.\n'
             '-Waiting insurance: A insurance who has applied for the insurance and whose invoice is going to be created.\n'
             '-Invoiced insurance: A insurance whose invoice has been created.\n'
             '-Paying insurance: A insurance who has paid the insurance fee.')
    insurance_start = fields.Date(compute='_compute_insurance_start',
        string ='Insurance Start Date',
        help="Date from which insurance becomes active.")
    insurance_stop = fields.Date(compute='_compute_insurance_stop',
        string ='Insurance End Date', 
        help="Date until which insurance remains active.")
    insurance_cancel = fields.Date(compute='_compute_insurance_cancel',
        string ='Cancel insurance Date', store=True,
        help="Date on which insurance has been cancelled")

    @api.depends('insurance_lines.account_invoice_line.invoice_id.state',
                 'insurance_lines.account_invoice_line.invoice_id.invoice_line_ids',
                 'insurance_lines.account_invoice_line.invoice_id.payment_ids',
                 'insurance_lines.account_invoice_line.invoice_id.payment_move_line_ids',
                 'insurance_lines.account_invoice_line.invoice_id.partner_id',
                 'insurance_lines.date_to', 'insurance_lines.date_from')
    def _compute_insurance_state(self):
        values = self._insurance_state()
        for partner in self:
            partner.insurance_state = values[partner.id]

        # Do not depend directly on "associate_member.insurance_state" or we might end up in an
        # infinite loop. Since we still need this dependency somehow, we explicitly search for the
        # "parent insurances" and trigger a recompute.
        parent_insurances = self.search([('associate_member', 'in', self.ids)]) - self
        if parent_insurances:
            parent_insurances._recompute_todo(self._fields['insurance_state'])

    @api.depends('insurance_lines.account_invoice_line.invoice_id.state',
                 'insurance_lines.account_invoice_line.invoice_id.invoice_line_ids',
                 'insurance_lines.account_invoice_line.invoice_id.payment_ids',
                 'insurance_lines.date_to', 'insurance_lines.date_from', 'insurance_lines.date_cancel',
                 'insurance_state',
                 'associate_member.insurance_state')
    def _compute_insurance_start(self):
        """Return  date of insurance"""
        for partner in self:
            partner.insurance_start = self.env['insurance.insurance_line'].search([
                ('partner', '=', partner.associate_member.id or partner.id), ('date_cancel','=',False)
            ], limit=1, order='date_from').date_from

    @api.depends('insurance_lines.account_invoice_line.invoice_id.state',
                 'insurance_lines.account_invoice_line.invoice_id.invoice_line_ids',
                 'insurance_lines.account_invoice_line.invoice_id.payment_ids',
                 'insurance_lines.date_to', 'insurance_lines.date_from', 'insurance_lines.date_cancel',
                 'insurance_state',
                 'associate_member.insurance_state')
    def _compute_insurance_stop(self):
        InsuranceLine = self.env['insurance.insurance_line']
        for partner in self:
            partner.insurance_stop = self.env['insurance.insurance_line'].search([
                ('partner', '=', partner.associate_member.id or partner.id),('date_cancel','=',False)
            ], limit=1, order='date_to desc').date_to

    @api.depends('insurance_lines.account_invoice_line.invoice_id.state',
                 'insurance_lines.account_invoice_line.invoice_id.invoice_line_ids',
                 'insurance_lines.account_invoice_line.invoice_id.payment_ids',
                 'insurance_lines.date_to', 'insurance_lines.date_from', 'insurance_lines.date_cancel',
                 'insurance_state',
                 'associate_member.insurance_state')
    def _compute_insurance_cancel(self):
        for partner in self:
            partner.insurance_cancel = self.env['insurance.insurance_line'].search([
                ('partner', '=', partner.id)
            ], limit=1, order='date_cancel desc').date_cancel

    def _insurance_state(self):
        """This Function return insurance State For Given Partner. """
        res = {}
        today = fields.Date.today()
        for partner in self:
            res[partner.id] = 'none'

            if partner.associate_member:
                res_state = partner.associate_member._insurance_state()
                res[partner.id] = res_state[partner.associate_member.id]
                continue

            s = 4
            if partner.insurance_lines:
                for mline in partner.insurance_lines.sorted(key=lambda r: r.id):
                    if (mline.date_to or date.min) >= today and (mline.date_from or date.min) <= today:
                        if mline.account_invoice_line.invoice_id.partner_id == partner:
                            mstate = mline.account_invoice_line.invoice_id.state
                            if mstate == 'paid':
                                inv = mline.account_invoice_line.invoice_id
                                for ml in inv.payment_move_line_ids:
                                    if any(ml.invoice_id.filtered(lambda inv: inv.type == 'out_refund')):
                                        s = 2
                                    else:
                                        s = 0
                            elif mstate == 'open' and s != 0:
                                s = 1
                            elif mstate == 'cancel' and s != 0 and s != 1:
                                s = 2
                            elif mstate == 'draft' and s != 0 and s != 1:
                                s = 3
                        """
                            If we have a line who is in the period and paid,
                            the line is valid and can be used for the insurance status.
                        """
                        if s == 0:
                            break
                    else:
                        if mline.account_invoice_line.invoice_id.partner_id == partner:
                            mstate = mline.account_invoice_line.invoice_id.state
                            if mstate == 'paid':
                                s = 5
                            else:
                                s = 6
                if s == 4:
                    for mline in partner.insurance_lines:
                        if (mline.date_from or date.min) < today and (mline.date_to or date.min) < today and (mline.date_from or date.min) <= (mline.date_to or date.min) and mline.account_invoice_line and mline.account_invoice_line.invoice_id.state == 'paid':
                            s = 5
                        else:
                            s = 6
                if s == 0:
                    res[partner.id] = 'paid'
                elif s == 1:
                    res[partner.id] = 'invoiced'
                elif s == 2:
                    res[partner.id] = 'canceled'
                elif s == 3:
                    res[partner.id] = 'waiting'
                elif s == 5:
                    res[partner.id] = 'old'
                elif s == 6:
                    res[partner.id] = 'none'
        return res

    

    @api.model
    def _cron_update_insurance(self):
        partners = self.search([('insurance_state', 'in', ['invoiced', 'paid'])])
        # mark the field to be recomputed, and recompute it
        partners._recompute_todo(self._fields['insurance_state'])
        self.recompute()

    @api.multi
    def create_insurance_invoice(self, product_id=None, datas=None):
        """ Create Customer Invoice of insurance for partners.
        @param datas: datas has dictionary value which consist Id of Insurance product and Cost Amount of Insurance.
                      datas = {'insurance_product_id': None, 'amount': None}
        """
        product_id = product_id or datas.get('insurance_product_id')
        amount = datas.get('amount', 0.0)
        invoice_list = []
        for partner in self:
            addr = partner.address_get(['invoice'])
            if not addr.get('invoice', False):
                raise UserError(_("Partner doesn't have an address to make the invoice."))
            if partner.date_end:
                invoice = self.env['account.invoice'].create({
                    'partner_id': partner.id,
                    'type': 'out_refund',
                    'account_id': partner.property_account_receivable_id.id,
                    'fiscal_position_id': partner.property_account_position_id.id
                })
            elif partner.date_start:
                invoice = self.env['account.invoice'].create({
                    'partner_id': partner.id,
                    'type': 'out_invoice',
                    'account_id': partner.property_account_receivable_id.id,
                    'fiscal_position_id': partner.property_account_position_id.id
                })
            else:
                invoice = self.env['account.invoice'].create({
                    'partner_id': partner.id,
                    'account_id': partner.property_account_receivable_id.id,
                    'fiscal_position_id': partner.property_account_position_id.id
                })
            line_values = {
                'product_id': product_id,
                'price_unit': amount,
                'invoice_id': invoice.id,
            }
            # create a record in cache, apply onchange then revert back to a dictionnary
            invoice_line = self.env['account.invoice.line'].new(line_values)
            invoice_line._onchange_product_id()
            line_values = invoice_line._convert_to_write({name: invoice_line[name] for name in invoice_line._cache})
            line_values['price_unit'] = amount
            invoice.write({'invoice_line_ids': [(0, 0, line_values)]})
            invoice_list.append(invoice.id)
            invoice.compute_taxes()
        
        # Add extra products
        for invoice in self.env['account.invoice'].browse(invoice_list):
            for line in invoice.invoice_line_ids:
                for insurance_product in line.product_id.insurance_product_ids:
                    # create a record in cache, apply onchange then revert back to a dictionnary
                    invoice_line = self.env['account.invoice.line'].new({'product_id': insurance_product.id,'price_unit': insurance_product.lst_price,'inovice_id':invoice.id})
                    invoice_line._onchange_product_id()
                    line_values = invoice_line._convert_to_write({name: invoice_line[name] for name in invoice_line._cache})
                    line_values['name'] = insurance_product.name
                    line_values['account_id'] = insurance_product.property_account_income_id.id if insurance_product.property_account_income_id else self.env['account.account'].search([('user_type_id','=',self.env.ref('account.data_account_type_revenue').id)])[0].id 
                    invoice.write({'invoice_line_ids': [(0, 0, line_values)]})
        # Calculate amount and qty
        for invoice in self.env['account.invoice'].browse(invoice_list):
            for line in invoice.invoice_line_ids:
                if line.product_id.insurance_code:
                    line.price_unit,line.quantity = line.product_id.insurance_get_amount_qty(invoice.partner_id)
        return invoice_list

