import logging
from odoo import models, fields, api, _
from datetime import date
from dateutil.relativedelta import relativedelta

_logger = logging.getLogger(__name__)


class MembershipLine(models.Model):
    _inherit = 'membership.membership_line'

    network_id = fields.Many2one('membership.network', string='Network')

    associate_member_id = fields.Many2one(
        'res.partner',
        string='Associate Member',
        help='The company or partner who covered this membership fee.',
    )
    invoice_state = fields.Selection(related='account_invoice_id.state', string='Invoice State', store=True)
    invoice_payment_state = fields.Selection(related='account_invoice_id.payment_state', string='Payment Status', store=True)

    @api.depends(
        'account_invoice_id.state',
        'account_invoice_id.amount_residual',
        'account_invoice_id.payment_state',
    )
    def _compute_state(self):
        # Filter only lines that have an invoice to avoid empty IN () SQL error
        lines_with_invoice = self.filtered('account_invoice_id')
        lines_without_invoice = self - lines_with_invoice

        # Handle lines without invoice (free members created directly)
        for line in lines_without_invoice:
            line.state = 'free' if not line.account_invoice_line else 'none'

        # Let Odoo handle the rest normally
        if lines_with_invoice:
            super(MembershipLine, lines_with_invoice)._compute_state()

    def action_renew_membership(self):
        """
        Renew selected membership lines (static memberships).
        Only renews if the product has a newer date range and the partner
        doesn't already have an active/invoiced membership for that new period.
        """
        today = date.today()
        for line in self:
            product = line.membership_id
            if product.is_rolling:
                continue
            
            # 1. Ensure product has a NEWER date range than this line
            if not product.membership_date_to or product.membership_date_to <= (line.date_to or date.min):
                continue
            
            # 2. Ensure the product's new range is currently valid or in the future
            if product.membership_date_to < today:
                continue

            # 3. Check if they already have a line for this NEW period (or any future period)
            # We check for any line that is not canceled and covers the new end date.
            existing = self.search_count([
                ('partner', '=', line.partner.id),
                ('membership_id', '=', product.id),
                ('network_id', '=', line.network_id.id),
                ('date_to', '>=', product.membership_date_to),
                ('state', 'not in', ['canceled']),
            ])
            if existing:
                continue

            # 4. Double check the partner isn't globally marked as a free member
            if line.partner.free_member:
                continue

            line.partner.with_context(
                membership_network_id=line.network_id.id,
                membership_join_date=product.membership_date_from,
            ).create_membership_invoice(
                product=product,
                amount=product.list_price
            )
        return True

    def action_send_invoice(self):
        """
        Server action to send the associated invoice of a membership line.
        """
        
        invoices = self.filtered(
            lambda membership: membership.invoice_payment_state == 'not_paid' and membership.invoice_state == 'posted'
        ).mapped('account_invoice_id')

        _logger.debug(f"{invoices}, {len(invoices)}")

        if invoices:
            return {
                'name': _("Print & Send"),
                'type': 'ir.actions.act_window',
                'view_mode': 'form',
                'res_model': 'account.move.send.wizard' if len(invoices) == 1 else 'account.move.send.batch.wizard',
                'target': 'new',
                'context': {
                    'active_model': 'account.move',
                    'active_ids': invoices.ids,
                },
            }

        # for line in self:
        #     invoice = line.account_invoice_id
        #     if invoice and invoice.state == 'posted':
        #         return invoice.action_invoice_sent()
        # return True

    @api.model
    def _cron_send_expiration_reminders(self):
        today = date.today()
        networks = self.env['membership.network'].search([
            ('mail_template_id', '!=', False),
            ('days_before_expiration', '>', 0)
        ])
        for network in networks:
            reminder_date = today + relativedelta(days=network.days_before_expiration)
            lines_to_remind = self.search([
                ('network_id', '=', network.id),
                ('date_to', '=', reminder_date),
                ('state', 'in', ['paid', 'invoiced', 'free']),
            ])
            for line in lines_to_remind:
                network.mail_template_id.send_mail(line.id, force_send=True)
        return True

    def action_confirm_invoices(self):
        invoices = self.filtered(
            lambda l: l.invoice_state == 'draft'
        ).mapped('account_invoice_id')
        if invoices:
            invoices.action_post()

    def _send_invoice_automatically(self):
        """Send invoices directly without wizard, for automated/cron context."""
        invoices = self.filtered(
            lambda l: l.invoice_payment_state == 'not_paid' and l.invoice_state == 'posted'
        ).mapped('account_invoice_id')

        if invoices:
            self.env['account.move.send']._generate_and_send_invoices(
                invoices,
                allow_fallback_pdf=True,
            )