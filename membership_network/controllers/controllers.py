from odoo import http
from odoo.http import request
from odoo.addons.website_event.controllers.main import WebsiteEventController
from odoo.exceptions import UserError


class MembershipNetworkEventController(WebsiteEventController):

    @http.route(['/event/<model("event.event"):event>/registration/confirm'], type='http', auth="public", methods=['POST'], website=True)
    def registration_confirm(self, event, **post):
        """
        Override registration confirmation to check network membership requirement
        """
        # Check if event requires membership
        if event.network_id:
            # Try to find partner from:
            # 1. Current logged-in user
            # 2. Email from registration form (first attendee)
            partner = None
            email = None
            
            # Check logged-in user first
            if not request.env.user._is_public():
                partner = request.env.user.partner_id
            
            # If not logged in, try to find partner by email from form
            if not partner:
                # Get email from first registration (format: '1-email-<question_id>')
                for key, value in post.items():
                    if '-email-' in key and value:
                        email = value
                        break
                
                if email:
                    # Search for partner with this email
                    partner = request.env['res.partner'].sudo().search([
                        ('email', '=', email)
                    ], limit=1)
            
            # Check if partner is a network member
            if not partner or partner not in event.network_id.sudo().member_ids:
                return request.render('membership_network.event_membership_required', {
                    'event': event,
                    'network': event.network_id.sudo(),
                    'partner': partner,
                    'email': email,
                })
        
        # If validation passes, proceed with normal registration
        return super().registration_confirm(event, **post)
