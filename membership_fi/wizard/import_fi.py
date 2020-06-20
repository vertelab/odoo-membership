# Copyright 2019 Ecosoft Co., Ltd (http://ecosoft.co.th/)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html)

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError, RedirectWarning


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
    data = fields.Binary(
        string='File',
        readonly=True,
    )
    template_id = fields.Many2one(
        'xlsx.template',
        string='Template',
        required=True,
        ondelete='cascade',
        domain=lambda self: self._context.get('template_domain', []),
    )
    res_id = fields.Integer(
        string='Resource ID',
        readonly=True,
        required=True,
    )
    res_model = fields.Char(
        string='Resource Model',
        readonly=True,
        required=True,
        size=500,
    )
    state = fields.Selection(
        [('choose', 'Choose'),
         ('get', 'Get')],
        default='choose',
        help="* Choose: wizard show in user selection mode"
             "\n* Get: wizard show results from user action",
    )

    @api.model
    def default_get(self, fields):
        res_model = self._context.get('active_model', False)
        res_id = self._context.get('active_id', False)
        template_domain = self._context.get('template_domain', [])
        templates = self.env['xlsx.template'].search(template_domain)
        if not templates:
            raise ValidationError(_('No template found'))
        defaults = super(ExportXLSXWizard, self).default_get(fields)
        for template in templates:
            if not template.datas:
                raise ValidationError(_('No file in %s') % (template.name,))
        defaults['template_id'] = len(templates) == 1 and templates.id or False
        defaults['res_id'] = res_id
        defaults['res_model'] = res_model
        return defaults




    @api.model
    def default_get(self, fields):
        res_model = self._context.get('active_model', False)
        res_id = self._context.get('active_id', False)
        template_domain = self._context.get('template_domain', [])
        templates = self.env['xlsx.template'].search(template_domain)
        if not templates:
            raise ValidationError(_('No template found'))
        defaults = super(ImportXLSXWizard, self).default_get(fields)
        for template in templates:
            if not template.datas:
                act = self.env.ref('excel_import_export.action_xlsx_template')
                raise RedirectWarning(
                    _('File "%s" not found in template, %s.') %
                    (template.fname, template.name),
                    act.id, _('Set Templates'))
        defaults['template_id'] = len(templates) == 1 and template.id or False
        defaults['res_id'] = res_id
        defaults['res_model'] = res_model
        return defaults


    @api.multi
    def action_import(self):
        self.ensure_one()
        Import = self.env['xlsx.import']
        res_ids = []
        if self.import_file:
            record = Import.import_xlsx(self.import_file, self.template_id,
                                        self.res_model, self.res_id)
            res_ids = [record.id]
        elif self.attachment_ids:
            for attach in self.attachment_ids:
                record = Import.import_xlsx(attach.datas, self.template_id)
                res_ids.append(record.id)
        else:
            raise ValidationError(_('Please select Excel file to import'))
        # If redirect_action is specified, do redirection
        if self.template_id.redirect_action:
            vals = self.template_id.redirect_action.read()[0]
            vals['domain'] = [('id', 'in', res_ids)]
            return vals
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
