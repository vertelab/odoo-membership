from odoo import models, fields, api, _


class IrUiView(models.Model):
    _inherit = 'ir.ui.view'

    mass_mailing_template = fields.Boolean(string='Mass Mailing Template')