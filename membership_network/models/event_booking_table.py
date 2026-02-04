from random import randint
from odoo import models, fields, api, _
from odoo.exceptions import UserError, AccessError, ValidationError
import logging

_logger = logging.getLogger(__name__)

class BookingTable(models.Model):
    _name = 'event.booking.table'
    _description = 'Event Booking Table'


    name = fields.Char(string="Name")
    capacity = fields.Integer(string="Capacity")
    color = fields.Integer(default=lambda dummy: randint(1, 11))


class BookingTableHistory(models.Model):
    _name = 'event.booking.table.history'
    _description = 'Event Booking Table History'


    name = fields.Char(string="Name")
    table_id = fields.Many2one(comodel_name='event.booking.table', string="Table")
    partner_ids = fields.Many2many(comodel_name='res.partner', string="Partner")
    event_id = fields.Many2one(comodel_name='event.event', string="Event")

    @api.depends('table_id', 'event_id')
    def _compute_table_name(self):
        for rec in self:
            rec.name = f'{rec.event_id.name} - {rec.table_id.name}'

