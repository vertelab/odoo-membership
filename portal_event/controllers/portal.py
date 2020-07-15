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

    def _prepare_portal_layout_values(self):
        values = super(CustomerPortal, self)._prepare_portal_layout_values()
        partner = request.env.user.partner_id
        
        if request.httprequest.method == 'POST':
            raise Warning(request.httprequest.environ)
            
        
        return values

    def Qaccount(self, redirect=None, **post):
        #raise Warning(post)
        response = super(CustomerPortal, self).account(redirect, post)
        return response
        
        
# ~ @http.route('/portal_event/event_type_tags, type='json', auth='public')
    # ~ def attachment_remove(self, tag_id, partner_id):
        # ~ """Remove the given `attachment_id`, only if it is in a "pending" state.

        # ~ The user must have access right on the attachment or provide a valid
        # ~ `access_token`.
        # ~ """
       # ~ partner = request.env["res.partner"].sudo().browse(partner_id)
       # ~ tag_ids = partner.event_type_tag_ids.mapped("id")
       
       
       # ~ #TODO: XOR på två 
       # ~ partner.event_type_tag_ids = (6, 0, tag_ids|tag_id)

        # ~ return error, error_message
