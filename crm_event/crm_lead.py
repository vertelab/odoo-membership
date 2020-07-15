# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _

class CrmLead(models.Model):
    _inherit = 'crm.lead'

    event_id = fields.Many2one(comodel_name='event.event') # domain|context|ondelete="'set null', 'restrict', 'cascade'"|auto_join|delegate

