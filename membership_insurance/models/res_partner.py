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
import logging
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

class res_partner(models.Model):
    _inherit = 'res.partner'

    liability_insurance = fields.Many2many(comodel_name='insurance.license', string='Insurance License')
    liability_insurance_permission = fields.Many2many(comodel_name='insurance.permission', string='Insurance Permission')
    company_role = fields.Many2one(comodel_name='insurance.role',string='Role') 
    internal_notes = fields.Text(string='Internal notes')
    date_start = fields.Datetime(string = "Date Start")
    date_end = fields.Datetime(string = "Date End")
    # ~ status = fields.Boolean(string="Aktive")
    # ~ space = fields.Char('  ', readonly=True)
    # ~ postnumber = fields.Char(string='ZIP')
    


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
        # return values in result, as this method is used by _fields_sync()
        return {}
        
    
    def _fields_sync(self, values):
        """ Sync commercial fields and address fields from company and to children after create/update,
        just as if those were all modeled as fields.related to the parent """
        return 
        
