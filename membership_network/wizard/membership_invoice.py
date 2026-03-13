# wizard/membership_invoice.py
from odoo import api, fields, models, _
from odoo.exceptions import UserError


class MembershipInvoice(models.TransientModel):
    _inherit = 'membership.invoice'

    join_date = fields.Date(
        string='Join Date',
        required=True,
        default=fields.Date.today,
    )
    associate_member_id = fields.Many2one(
        'res.partner',
        string='Associate Member',
        help='The company who has covered this membership fee.',
    )
    network_id = fields.Many2one(
        'membership.network',
        string='Network',
    )

    # -------------------------------------------------------------------------
    # Onchange
    # -------------------------------------------------------------------------

    @api.onchange('product_id')
    def _onchange_product_network(self):
        self.network_id = False
        if self.product_id:
            networks = self.env['membership.network'].search([
                ('product_ids', 'in', self.product_id.id)
            ])
            return {'domain': {'network_id': [('id', 'in', networks.ids)]}}

    @api.onchange('associate_member_id')
    def _onchange_associate_member(self):
        if not self.associate_member_id:
            return
        active_line = self._get_associate_active_line()
        if active_line:
            self.product_id = active_line.membership_id
            self.member_price = active_line.member_price
        else:
            return {
                'warning': {
                    'title': _('No Active Membership'),
                    'message': _(
                        '%s does not have an active paid membership. '
                        'The member will be invoiced normally.'
                    ) % self.associate_member_id.name,
                }
            }

    # -------------------------------------------------------------------------
    # Helpers
    # -------------------------------------------------------------------------

    def _get_associate_active_line(self, product_id=None):
        """Get associate's active membership line, optionally filtered by product."""
        if not self.associate_member_id:
            return False
        domain = [
            ('partner', '=', self.associate_member_id.id),
            ('state', 'in', ['paid', 'invoiced']),
        ]
        if product_id:
            domain.append(('membership_id', '=', product_id.id))
        return self.env['membership.membership_line'].search(
            domain, limit=1, order='date_to desc'
        )

    def _associate_covers_product(self):
        """Check if associate has an active line for the selected product."""
        if not self.associate_member_id or not self.product_id:
            return False
        return bool(self._get_associate_active_line(product_id=self.product_id))

    def _get_partners(self):
        """Return partners to process from active_ids context."""
        return self.env['res.partner'].browse(self._context.get('active_ids', []))

    def _filter_eligible_partners(self, partners):
        """
        Split partners into eligible and skipped.
        Skipped if they already have an active membership for this product/network.
        Returns (to_process, skipped_names)
        """
        to_process = self.env['res.partner']
        skipped = []

        for partner in partners:
            existing = self.env['membership.membership_line'].search([
                ('partner', '=', partner.id),
                ('membership_id', '=', self.product_id.id),
                ('network_id', '=', self.network_id.id if self.network_id else False),
                ('state', 'in', ['paid', 'invoiced', 'waiting']),
            ], limit=1)
            if existing:
                skipped.append(partner.name)
            else:
                to_process |= partner

        return to_process, skipped

    def _notify_skipped(self, skipped, next_action=None):
        """Return a sticky warning notification listing skipped partners."""
        params = {
            'title': _('Some Partners Skipped'),
            'message': _('Already active members, skipped: %s') % ', '.join(skipped),
            'type': 'warning',
            'sticky': True,
        }
        if next_action:
            params['next'] = next_action
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': params,
        }

    def _create_associate_membership_line(self, partner, active_line):
        """Create a membership line directly for a partner under an associate."""
        if partner.free_member:
            return False, '%s (free member)' % partner.name

        existing = self.env['membership.membership_line'].search([
            ('partner', '=', partner.id),
            ('associate_member_id', '=', self.associate_member_id.id),
            ('membership_id', '=', self.product_id.id),
            ('state', 'in', ['paid', 'invoiced']),
        ], limit=1)
        if existing:
            return False, partner.name

        self.env['membership.membership_line'].create({
            'partner': partner.id,
            'membership_id': active_line.membership_id.id,
            'member_price': active_line.member_price,
            'date': self.join_date,
            'date_from': active_line.date_from,
            'date_to': active_line.date_to,
            'account_invoice_line': active_line.account_invoice_line.id,
            'associate_member_id': self.associate_member_id.id,
            'network_id': self.network_id.id if self.network_id else False,
        })
        return True, None

    # -------------------------------------------------------------------------
    # Main action
    # -------------------------------------------------------------------------

    def membership_invoice(self):
        partners = self._get_partners()
        to_process, skipped = self._filter_eligible_partners(partners)

        if not to_process:
            raise UserError(_('All selected partners already have an active membership for this plan.'))

        if self._associate_covers_product():
            return self._membership_invoice_associate(to_process, skipped)
        return self._membership_invoice_normal(to_process, skipped)

    def _membership_invoice_normal(self, to_process, skipped):
        """Normal invoice flow — create invoice for each partner."""
        self = self.with_context(
            active_ids=to_process.ids,
            membership_join_date=self.join_date,
            membership_associate_member_id=self.associate_member_id.id if self.associate_member_id else False,
            membership_network_id=self.network_id.id if self.network_id else False,
        )
        action = super().membership_invoice()

        if skipped:
            return self._notify_skipped(skipped, next_action=action)
        return action

    def _membership_invoice_associate(self, to_process, skipped):
        """Associate covers product — create membership lines directly, no invoice."""
        active_line = self._get_associate_active_line(product_id=self.product_id)

        for partner in to_process:
            success, skip_reason = self._create_associate_membership_line(partner, active_line)
            if not success:
                skipped.append(skip_reason)

        if skipped:
            return self._notify_skipped(skipped)
        return {'type': 'ir.actions.act_window_close'}