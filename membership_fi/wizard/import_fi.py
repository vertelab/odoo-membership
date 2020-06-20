# Copyright 2019 Ecosoft Co., Ltd (http://ecosoft.co.th/)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html)

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError, RedirectWarning

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

        filestr = base64.decodestring(self.import_file).strip()
        raise Warning(u"%s" % filestr[3:].strip())
        f = StringIO(u"%s" % filestr[3:].strip())
        reader = csv.DictReader(f, delimiter=';')





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
