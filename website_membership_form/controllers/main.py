# -*- coding: utf-8 -*-

import babel.dates
import re
import werkzeug
import json

from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta

import logging

from odoo import fields, http, _
from odoo.addons.http_routing.models.ir_http import slug
from odoo.http import content_disposition, request
_logger = logging.getLogger(__name__)

class WebsiteEventController(http.Controller):
    @http.route(['/form'], type='http', auth="public", website=True, sitemap=False)
    def form_page(self, **post):
        return request.render('website_event_test.index')

    @http.route('/form/post', type="http", auth='public',  methods=['POST'])
    def save_form_data(self, **post):
        partner = http.request.env['res.partner']
        partner.create({"name" : post["name"], "phone" : post["phone"], "contact_address" : post["address"]})
