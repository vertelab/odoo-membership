import logging
import random
from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError

_logger = logging.getLogger(__name__)

class EventType(models.Model):
    _inherit = 'event.type'

    event_table_ids = fields.Many2many("event.booking.table", string="Tables")
    network_id = fields.Many2one('membership.network', string='Network',
        help='Link this event to a membership network to invite all members')
    mass_mailing_template_id = fields.Many2one('ir.ui.view', domain="[('mass_mailing_template', '=', True)]")