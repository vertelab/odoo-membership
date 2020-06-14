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
import logging

_logger = logging.getLogger(__name__)


class insurance_permission(models.Model):
    _name = 'insurance.permission'
    
    name = fields.Char(string="Name")
    
class insurance_license(models.Model):
    _name = 'insurance.license'
    
    name = fields.Char(string="Name")

class res_partner(models.Model):
    _inherit = 'res.partner'

    liability_insurance = fields.Many2many(comodel_name='insurance.license', string='Insurance License')
    liability_insurance_permission = fields.Many2many(comodel_name='insurance.permission', string='Insurance Permission')
    
    # ~ have_life_insurance = fields.Boolean(string='Life Insurance', default=False, help='This is life insurance')
    # ~ have_property_insurance=fields.Boolean(string='Property Insurance', default=False, help='This is property insurance')
    # ~ insurance_permission_ids = fields.Many2many(comodel_name='res.partner', string='Permission')
    # ~ membership_ids = fields.Many2many(comodel_name='res.partner', relation='partner_member_rel', column1='parent_id',column2='member_id', string='Membership ID')
    # ~ count_fellowship = fields.Integer(string='Fellowship', compute ='_compute_count_fellowship')
    count_company = fields.Integer(string='Company', compute ='_compute_count_company')
    count_accommodator = fields.Integer(string='Accommodators', compute ='_compute_count_accommodator')
    count_life_insurance = fields.Integer(string='Life Insurance', compute ='_compute_count_life_insurance')
    count_property_insurance = fields.Integer(string='Property Insurance', compute ='_compute_count_property_insurance')
    count_life_protperty_insurance = fields.Integer(string='Life/Property Insurance', compute ='_compute_life_protperty_insurance')
    vat = fields.Char(string='Tax ID', help="The Tax Identification Number. Complete it if the contact is subjected to government taxes. Used in some legal statements.")
    personnumber = fields.Char(string='Person Number', help="This is person number")
    org_prn = fields.Char(string="Org/Person Number", compute ='_compute_org_prn')
    # ~ company_type = fields.Selection(selection_add=[('fellowship', 'Fellowship'), ('accommodator', 'Accommodator')])
    url_financial_supervisory = fields.Text(string = 'Finansinspektionen')
    
    insurance_company_type = fields.Selection(string='Company Type',
        selection=[('person', 'Individual'),('fellowship', 'Fellowship'),('company', 'Company'),('accomodator', 'Accomodator')],
        inverse='_insurance_write_company_type')

    @api.onchange('insurance_company_type')
    def onchange_insurance_company_type(self):
        self.is_company = (self.insurance_company_type not in ['person','accomodator'])
        self.company_type = 'company' if self.is_company else 'person'


    def _insurance_write_company_type(self):
        for partner in self:
            partner.is_company = (partner.insurance_company_type not in ['person','accomodator'])
            partner.company_type = 'company' if partner.is_company else 'person'





    
    @api.one
    def _compute_org_prn(self):
        if self.company_type == 'company':
            self.org_prn = self.vat
        elif self.company_type == 'person':
            self.org_prn = self.personnumber
    
    def _compute_count_company(self):
        self.count_company = self.env['res.partner'].search_count([('id', 'child_of', self.id),('insurance_company_type', '=', 'fellowship')])
    
    def _compute_count_accommodator(self):
        self.count_accommodator = self.env['res.partner'].search_count([('id', 'child_of', self.id),('insurance_company_type', '=', 'accomodator')])
    
    def _compute_count_life_insurance(self):
        self.count_life_insurance = self.env['res.partner'].search_count([('id', 'child_of', self.id),('liability_insurance', '=', self.env.ref('membership_insurance.crm_insurance_life').id)])
    
    def _compute_count_property_insurance(self):
        self.count_property_insurance = self.env['res.partner'].search_count([('id', 'child_of', self.id),('liability_insurance', '=', self.env.ref('membership_insurance.crm_insurance_property').id)])
    
    def _compute_life_protperty_insurance(self):
        self.count_life_protperty_insurance = self.env['res.partner'].search_count([('id', 'child_of', self.id),('liability_insurance', '=', self.env.ref('membership_insurance.crm_insurance_life').id),('liability_insurance', '=', self.env.ref('membership_insurance.crm_insurance_property').id)])
        
    def _compute_count_life_permission(self):
        self.count_life_permission = self.env['res.partner'].search_count([('id', 'child_of', self.id),('liability_insurance_permission', '=', self.env.ref('membership_insurance.crm_insurance_life_permission').id)])
    
    def _compute_count_property_permission(self):
        self.count_property_permission = self.env['res.partner'].search_count([('id', 'child_of', self.id),('liability_insurance_permission', '=', self.env.ref('membership_insurance.crm_insurance_property_permission').id)])
    
    def _compute_life_protperty_permission(self):
        self.count_life_protperty_insurance_permission = self.env['res.partner'].search_count([('id', 'child_of', self.id),('liability_insurance_permission', '=', self.env.ref('membership_insurance.crm_insurance_life_permission').id),('liability_insurance_permission', '=', self.env.ref('membership_insurance.crm_insurance_property_permission').id)])
        
    @api.multi
    def company_button(self):
        partner_ids = self.ids
        partner_ids.append(self.env.user.partner_id.id)
        action = self.env['ir.actions.act_window'].for_xml_id('contacts', 'action_contacts')
        action['context'] = {
            'default_partner_ids': partner_ids,
        }
        action['domain'] = [('id', 'child_of', self.id),('insurance_company_type', '=', 'company')]
        return action

    @api.multi
    def fellowship_button(self):
        action = self.env['ir.actions.act_window'].for_xml_id('contacts', 'action_contacts')
        action['domain'] = [('id', 'child_of', self.id),('insurance_company_type', '=', 'fellowship')]
        return action

        
    # ~ @api.multi
    # ~ def fellowship_button(self):
        # ~ partner_ids = self.ids
        # ~ partner_ids.append(self.env.user.partner_id.id)
        # ~ action = self.env['ir.actions.act_window'].for_xml_id('contacts', 'action_contacts')
        # ~ action['context'] = {
            # ~ 'default_partner_ids': partner_ids,
        # ~ }
        # ~ action['domain'] = [('id', 'child_of', self.id),('is_fellowship','=', True)]
        # ~ return action
    
    @api.multi
    def accommodator_button(self):
        partner_ids = self.ids
        partner_ids.append(self.env.user.partner_id.id)
        action = self.env['ir.actions.act_window'].for_xml_id('contacts', 'action_contacts')
        action['context'] = {
            'default_partner_ids': partner_ids,
        }
        action['domain'] = [('id', 'child_of', self.id),('insurance_company_type', '=', 'accomodator')]
        return action
    
    @api.multi
    def life_insurance_button(self):
        partner_ids = self.ids
        partner_ids.append(self.env.user.partner_id.id)
        action = self.env['ir.actions.act_window'].for_xml_id('contacts', 'action_contacts')
        action['context'] = {
            'default_partner_ids': partner_ids,
        }
        action['domain'] = [('id', 'child_of', self.id),('liability_insurance', '=', self.env.ref('membership_insurance.crm_insurance_life').id)]
        return action
        
    @api.multi
    def property_insurance_button(self):
        partner_ids = self.ids
        partner_ids.append(self.env.user.partner_id.id)
        action = self.env['ir.actions.act_window'].for_xml_id('contacts', 'action_contacts')
        action['context'] = {
            'default_partner_ids': partner_ids,
        }
        action['domain'] = [('id', 'child_of', self.id),('liability_insurance', '=', self.env.ref('membership_insurance.crm_insurance_property').id)]
        return action
        
    @api.multi
    def life_protperty_insurance_button(self):
        partner_ids = self.ids
        partner_ids.append(self.env.user.partner_id.id)
        action = self.env['ir.actions.act_window'].for_xml_id('contacts', 'action_contacts')
        action['context'] = {
            'default_partner_ids': partner_ids,
        }
        action['domain'] = [('id', 'child_of', self.id),('liability_insurance', '=', self.env.ref('membershipinsurance.crm_insurance_life').id),('liability_insurance', '=', self.env.ref('membership_insurance.crm_insurance_property').id)]
        return action
        
    @api.multi
    def life_permission_button(self):
        partner_ids = self.ids
        partner_ids.append(self.env.user.partner_id.id)
        action = self.env['ir.actions.act_window'].for_xml_id('contacts', 'action_contacts')
        action['context'] = {
            'default_partner_ids': partner_ids,
        }
        action['domain'] = [('id', 'child_of', self.id),('liability_insurance_permission', '=', self.env.ref('membership_insurance.crm_insurance_life_permission').id)]
        return action
        
    @api.multi
    def property_permission_button(self):
        partner_ids = self.ids
        partner_ids.append(self.env.user.partner_id.id)
        action = self.env['ir.actions.act_window'].for_xml_id('contacts', 'action_contacts')
        action['context'] = {
            'default_partner_ids': partner_ids,
        }
        action['domain'] = [('id', 'child_of', self.id),('liability_insurance_permission', '=', self.env.ref('membership_insurance.crm_insurance_property_permission').id)]
        return action
        
    @api.multi
    def life_protperty_permission_button(self):
        partner_ids = self.ids
        partner_ids.append(self.env.user.partner_id.id)
        action = self.env['ir.actions.act_window'].for_xml_id('contacts', 'action_contacts')
        action['context'] = {
            'default_partner_ids': partner_ids,
        }
        action['domain'] = [('id', 'child_of', self.id),('liability_insurance_permission', '=', self.env.ref('membership_insurance.crm_insurance_life_permission').id),('liability_insurance_permission', '=', self.env.ref('membership_insurance.crm_insurance_property_permission').id)]
        return action
        
    
   
