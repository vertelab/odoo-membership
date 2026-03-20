from datetime import date as date_type

from odoo import http, _
from odoo.http import request
from odoo.addons.portal.controllers.portal import CustomerPortal


class MembershipPortal(CustomerPortal):

    def _prepare_home_portal_values(self, counters):
        values = super()._prepare_home_portal_values(counters)
        if 'membership_count' in counters:
            partner = request.env.user.partner_id
            values['membership_count'] = request.env['membership.membership_line'].search_count([
                ('partner', '=', partner.id)
                # ('state', 'not in', ['none']),
            ])
        return values

    @http.route(['/my/memberships'], type='http', auth='user', website=True)
    def portal_memberships(self, **kw):
        partner = request.env.user.partner_id

        unpaid_lines = request.env['membership.membership_line'].search([
            ('partner', '=', partner.id),
            # ('state', 'not in', ['none', 'canceled']),
            ('invoice_payment_state', '=', 'not_paid'),
        ], order='date_from desc')

        other_lines = request.env['membership.membership_line'].search([
            ('partner', '=', partner.id),
            # ('state', 'not in', ['none', 'canceled']),
            ('invoice_payment_state', '!=', 'not_paid'),
        ], order='date_from desc')

        membership_lines = unpaid_lines | other_lines

        values = {
            'membership_lines': membership_lines,
            'page_name': 'membership',
        }
        return request.render('membership_network.portal_my_memberships', values)

    @http.route(['/my/memberships/<int:line_id>/cancel'], type='http', auth='user', website=True)
    def portal_membership_cancel(self, line_id, **kw):
        partner = request.env.user.partner_id
        line = request.env['membership.membership_line'].search([
            ('id', '=', line_id),
            ('partner', '=', partner.id),
            ('invoice_state', '=', 'posted'),
            ('invoice_payment_state', '=', 'not_paid'),
        ], limit=1)

        if not line:
            return request.redirect('/my/memberships')

        invoice = line.account_invoice_id
        if invoice:
            invoice.button_cancel()

        network = line.network_id
        if network:
            network.message_post(
                body=_('Member %s has cancelled their membership for %s.') % (
                    partner.name,
                    line.membership_id.name,
                ),
                message_type='notification',
                subtype_xmlid='mail.mt_note',
            )

        return request.redirect('/my/memberships')