# -*- coding: utf-8 -*-

import logging
import pytz
import werkzeug

from odoo import api, fields, models, _
from odoo.addons.http_routing.models.ir_http import slug
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)

class Form(models.Model):
    _name = 'form.test'
    
    #_inherit = 'res.partner'

    #age = fields.Integer(string="Age", help="This is your age.")
