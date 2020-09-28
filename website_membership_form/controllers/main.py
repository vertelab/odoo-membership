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
        @http.route(['/memberform/<model("event.event"):event>/event'], type='http', auth="public", website=True, sitemap=False)
        def form_page(self, event, **post):
                return request.render('website_membership_form.index', {'event' : event})

        @http.route('/memberform/post/', type="http", auth='public', website=True, methods=['POST'])
        def save_form_data(self, **post):
                event = request.env['event.event'].sudo().browse(int(post['event_id']))
                crm_lead = request.env['crm.lead'].sudo().create({"name" : 'N/A', "type" : "lead", "mobile" : post["mobile"], 
                                                        "email_from" : post["email_from"], "event_id" : int(post["event_id"]),
                                                        })
                crm_lead.tag_ids = [(6,0,[tag.id for tag in request.env['crm.lead.tag'].search([]) if tag.name in event.event_type_id.event_type_tag_ids.mapped('name')])]
                return request.render('website_membership_form.thankyou', {'event' : event})
