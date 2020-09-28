# -*- coding: utf-8 -*-

import logging
import pytz
import werkzeug

from odoo import api, fields, models, _
from odoo.addons.http_routing.models.ir_http import slug
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)

