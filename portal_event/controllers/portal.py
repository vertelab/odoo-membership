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
import logging
_logger = logging.getLogger(__name__)


class CustomerPortal(CustomerPortal):

    @http.route('/portal_event/event_type_tags', type='json', auth='public')
    def attachment_remove(self, **post):
        
        #list of changed id
        tag_id = post['id']
        
        partner = request.env.user
        #list of ids
        tag_ids = partner.event_type_tag_ids.mapped("id")
        
        l3 = []
        l1 = tag_ids
        l2 =  [int(tag_id[0])]
        
        for x in l1:
            if not x in l2:
                l3.append(x)
        for y in l2:
            if not y in l1:
                l3.append(y)

        partner.event_type_tag_ids = [(6, 0, l3)]
        
