# Copyright 2019 Ecosoft Co., Ltd (http://ecosoft.co.th/)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html)

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError, RedirectWarning
import logging
_logger = logging.getLogger(__name__)


import base64
from io import StringIO
import csv

class ImportFIWizard(models.TransientModel):
    """ This wizard is used with the template (xlsx.template) to import
    xlsx template back to active record """
    _name = 'import.fi.wizard'
    _description = 'Wizard for importing csv from FI'

    import_file = fields.Binary(
        string='Import File (*.csv)',
    )

    name = fields.Char(
        string='File Name',
        readonly=True,
        size=500,
    )
    datas = fields.Binary(
        string='File',
        readonly=True,
    )
    fname = fields.Binary(
        string='File',
        readonly=True,
    )
    
    state = fields.Selection(
        [('choose', 'Choose'),
         ('get', 'Get')],
        default='choose',
        help="* Choose: wizard show in user selection mode"
             "\n* Get: wizard show results from user action",
    )

    @api.multi
    def action_import(self):
        self.ensure_one()

        filestr = u'%s' % base64.decodestring(self.import_file)[3:].decode('utf-8').strip()
        f = StringIO(filestr)
        reader = csv.DictReader(f, delimiter=';')
        import_ids = []
        self.env['import.fi.company'].search([]).unlink()
        for rec in reader:
            if len(rec['Org.nummer'])>0:
                import_ids.append(self.env['import.fi.company'].add_new(rec).id)
            
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'import.fi.company',
            'view_mode': 'form',
            'view_type': 'form',
            'views': [(False, 'tree')],
        }


        action = self.env['ir.actions.act_window'].for_xml_id('membership_fi', 'action_import_fi_company')
        # ~ action['context'] = {
            # ~ 'default_partner_ids': partner_ids,
        # ~ }
        action['domain'] = [('id','in',import_ids)]
        # ~ raise Warning(action)
        return action



        raise ValidationError(_('Please select Excel file to import %s') % reader)
        # If redirect_action is specified, do redirection
        self.write({'state': 'get'})
        return {
            'type': 'ir.actions.act_window',
            'res_model': self._name,
            'view_mode': 'form',
            'view_type': 'form',
            'res_id': self.id,
            'views': [(False, 'form')],
            'target': 'new',
        }


class ImportFICompany(models.TransientModel):
    """ This wizard is used with the template (xlsx.template) to import
    xlsx template back to active record """
    _name = 'import.fi.company'
    _description = 'Companies from FI'


    name = fields.Char(string='Name', trim=True, )
    org_nr = fields.Char(string='Orgnr', size=11, trim=True, )
    main_type = fields.Char(string='Main type', size=64, trim=True, )
    other_type = fields.Char(string='Other type', size=64, trim=True, )
    permit_1 = fields.Char(string='Permit 1', size=64, trim=True, )
    permit_2 = fields.Char(string='Permit 2', size=64, trim=True, )
    permit_3 = fields.Char(string='Permit 3', size=64, trim=True, )
    etc = fields.Char(string='Etc', size=64, trim=True, )
    permit = fields.Text()
    member_id = fields.Many2one(comodel_name="res.partber")
    
    def add_new(self,rec):
        _logger.warn("keys %s" % rec.keys())
        permit_list = list(rec.values())[4:]
        permit = ';'.join([str(p) for p in permit_list])
        member = self.env['res.partner'].search([('org_nr','=',rec['Org.nummer'])])
        return self.env['import.fi.company'].create({'name':rec['Namn'], 'org_nr': rec['Org.nummer'], 'main_type':rec['Huvudverksamhet'],
                    'other_type': rec['Övriga verksamheter'], 'permit_1':rec['Tillstånd 1'], 'permit_2':rec['Tillstånd 2'], 
                    'permit_3':rec['Tillstånd 3'], 'etc':rec['et.c.'],'permit':permit,'member_id': member.id if member else None})
         
        
