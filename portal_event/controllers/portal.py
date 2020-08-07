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


class CustomerPortal(CustomerPortal):

    @http.route('/portal_event/event_type_tags', type='json', auth='public')
    def attachment_remove(self, **post):
        
        #list of 1 id
        tag_id = post['id']
        
        partner = request.env.user
        #list of ids
        tag_ids = partner.event_type_tag_ids.mapped("id")
        
        l3 = []
        l1 = tag_ids
        l2 =  tag_id
        for x in l1:
            if not x in l2:
                l3.append(x)
        for y in l2:
            if not y in l1:
                l3.append(y)


        
        
        partner.event_type_tag_ids = (6, 0, l3)
        
        
        
        #request.env['event.type.tag'].search(['id'=l3[0]])
        # ~ (1, ID, { values })    update the linked record with id = ID (write *values* on it)
        
        
        
        return error, error_message
        
    # ~ def _prepare_portal_layout_values(self):
        # ~ values = super(CustomerPortal, self)._prepare_portal_layout_values()
        # ~ partner = request.env.user.partner_id
        
        # ~ if request.httprequest.method == 'POST':
            # ~ raise Warning(request.httprequest.environ)
            
        
        # ~ return values

    # ~ def Qaccount(self, redirect=None, **post):
        # ~ #raise Warning(post)
        # ~ response = super(CustomerPortal, self).account(redirect, post)
        # ~ return response
        
    #/portal_event/<model("event.type.tags"):tag>/event_type_tags'     komplicerad länk
    
