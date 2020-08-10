# -*- coding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2020  (<anton@grand-moff-tarkin>)
#    All Rights Reserved
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as published
#    by the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
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

from odoo import models, fields, api, exceptions, _
import logging
_logger = logging.getLogger(__name__)


class EventType(models.Model):
    _inherit = 'event.type'
    event_type_tag_ids = fields.Many2many(comodel_name='event.type.tag',string='Taggar')
    description = fields.Html('description')

class ResPartner(models.Model):
    _inherit = 'res.partner'
    event_type_tag_ids = fields.Many2many(comodel_name='event.type.tag',string='Intressen',help='Intresseområden')
    
class EventTypeTag(models.Model):
    _name = 'event.type.tag'
    name = fields.Char(string='Name')
    
