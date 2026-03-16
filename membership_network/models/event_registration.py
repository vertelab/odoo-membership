import logging
from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError

_logger = logging.getLogger(__name__)


class EventRegistration(models.Model):
    _inherit = 'event.registration'

    session_1_table_id = fields.Many2one('event.booking.table', string="Session 1")
    session_1_table_code = fields.Char(string="Session 1 Code", related="session_1_table_id.code")

    session_2_table_id = fields.Many2one('event.booking.table', string="Session 2")
    session_2_table_code = fields.Char(string="Session 2 Code", related="session_2_table_id.code")

    session_3_table_id = fields.Many2one('event.booking.table', string="Session 3")
    session_3_table_code = fields.Char(string="Session 3 Code", related="session_3_table_id.code")

    network_id = fields.Many2one('membership.network', string="Network", related="event_id.network_id")
    network_name = fields.Char(string="Network Name", related="network_id.name")

    @api.model_create_multi
    def create(self, vals_list):
        registrations = super().create(vals_list)
        for registration in registrations:
            if not registration.partner_id and registration.email:
                partner = self.env['res.partner'].sudo().search([
                    ('email', '=', registration.email)
                ], limit=1)
                if partner:
                    registration.partner_id = partner
                elif registration.event_id.network_id:
                    raise UserError(_(
                        'No partner found with email "%s". '
                        'This event requires network membership. '
                        'Please ensure you are registered in the system.'
                    ) % registration.email)
                else:
                    partner = self.env['res.partner'].sudo().create({
                        'name': registration.name,
                        'email': registration.email,
                        'phone': registration.phone,
                        'company_type': 'person',
                    })
                    registration.partner_id = partner
        return registrations