import logging
from odoo import fields, models

_logger = logging.getLogger(__name__)


class MailingMailing(models.Model):
    _inherit = 'mailing.mailing'

    ref_object = fields.Reference(
        selection=lambda self: [
            (m.model, m.name) for m in self.env['ir.model'].sudo().search([])
        ],
        string='Reference',
    )