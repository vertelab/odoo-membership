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


class UtmCampaign(models.Model):
    _inherit = 'utm.campaign'
    start_date = fields.Date()
    end_date = fields.Date()
    description = fields.Text()
    campaign_codes = fields.Many2many(comodel_name='campaign.code',string='Campaign Code')
    
class CampaignCode(models.Model):
    _name = 'campaign.code'
    name = fields.Char(String='Name')

    


    
   
