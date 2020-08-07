# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

import binascii
from datetime import date

from odoo import fields, http, _
from odoo.exceptions import AccessError, MissingError
from odoo.http import request
from odoo.addons.payment.controllers.portal import PaymentProcessing
from odoo.addons.portal.controllers.mail import _message_post_helper
from odoo.addons.portal.controllers.portal import CustomerPortal, pager as portal_pager, get_records_pager
from odoo.osv import expression


import json
import random
import urllib.request


class CustomerPortal(CustomerPortal):

    @http.route(['/communication_preferences/change_preference'], type='json', auth="public", website=True)
    def change_preference(self, **kw):
        data = kw
        if data['id'] == 'email_checkbox':
            if data['checked']:
                request.env.user.allow_email = True
            else:
                request.env.user.allow_email = False
                
        if data['id'] == 'facebook_checkbox':
            if data['checked']:
                request.env.user.allow_facebook = True
            else:
                request.env.user.allow_facebook = False
                
        if data['id'] == 'sms_checkbox':
            if data['checked']:
                request.env.user.allow_sms = True
            else:
                request.env.user.allow_sms = False
                
        if data['id'] == 'twitter_checkbox':
            if data['checked']:
                request.env.user.allow_twitter = True
            else:
                request.env.user.allow_twitter = False
            


    
