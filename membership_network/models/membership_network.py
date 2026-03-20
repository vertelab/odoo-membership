from odoo import api, fields, models, tools, _
from datetime import date

class MembershipNetwork(models.Model):
    _name = 'membership.network'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    # _mailing_enabled = True
    _description = 'Membership Network'

    name = fields.Char(string='Name', required=True)
    description = fields.Text(string='Description')
    product_ids = fields.Many2many('product.product', string='Membership Product',
        domain=[('membership', '=', True)],
        help='Membership product for this network. Partners who purchase this product become members.')
    member_ids = fields.Many2many('res.partner', compute='_compute_members', string='Members', search='_search_member_ids',)
    member_count = fields.Integer(compute='_compute_member_count', string='Number of Members')
    active_member_count = fields.Integer(compute='_compute_member_count', string='Active Members')
    network_partner_id = fields.Many2one(
        'res.partner', string='Membership Partner', domain=[('is_network', '=', True)]
    )
    parent_id = fields.Many2one(
        'membership.network', string='Parent Membership Network', index=True,
        help='Select the membership network, if any.')
    child_ids = fields.One2many(
        'membership.network', 'parent_id', string='Sub Network',
        help='List of sub network, if any.')
    invite_only = fields.Boolean(string="Invite Only") 
    days_before_expiration = fields.Integer(string="Expiration Reminder Days", default=30)
    send_invoices_automatically = fields.Boolean(string="Send Invoices Automatically", default=False)
    mail_template_id = fields.Many2one('mail.template', string='Expiration Reminder Template', 
        domain=[('model_id.model', '=', 'membership.membership_line')],
        help="Email template sent to remind members about expiration.")
    
    membership_line_count = fields.Integer(
        compute='_compute_membership_line_count',
        string='Membership Lines',
    )

    def _compute_membership_line_count(self):
        for network in self:
            network.membership_line_count = self.env['membership.membership_line'].search_count([
                ('network_id', '=', network.id),
            ])

    def _compute_members(self):
        for network in self:
            network.member_ids = self.env['res.partner'].search([
                ('network_ids', 'in', network.id)
            ])

    @api.depends('member_ids', 'member_ids.membership_state')
    def _compute_member_count(self):
        for network in self:
            members = network.member_ids
            network.member_count = len(members)
            network.active_member_count = len(
                members.filtered(lambda p: p.membership_state in ['paid', 'invoiced', 'free'])
            )

    def _search_member_ids(self, operator, value):
        return [('product_ids.membership_line_ids.partner', operator, value)]

    def action_view_membership_lines(self):
        self.ensure_one()
        return {
            'name': 'Membership Lines',
            'type': 'ir.actions.act_window',
            'res_model': 'membership.membership_line',
            'view_mode': 'list,form',
            'domain': [('network_id', '=', self.id)],
            'search_view_id': self.env.ref('membership_network.view_membership_line_search').id,
            'context': {
                'default_network_id': self.id,
                'search_default_invoice_payment_state': 1,
            },
        }

    @api.model
    def _cron_renew_memberships(self):
        """Called by the cron job — runs across all networks."""
        all_networks = self.search([])
        all_networks.action_renew_memberships()

    def action_renew_memberships(self):
        """Operates on self (selected networks). Used by server action and cron."""
        today = date.today()

        static_products = self.env['product.product'].search([
            ('membership', '=', True),
            ('is_rolling', '=', False),
            ('membership_date_from', '!=', False),
            ('membership_date_to', '!=', False),
        ])
        for product in static_products:
            networks = self.filtered(lambda n: product in n.product_ids)
            for network in networks:
                expired_lines_domain = [
                    ('membership_id', '=', product.id),
                    ('network_id', '=', network.id),
                    ('date_to', '<', product.membership_date_to),
                    ('state', 'in', ['old', 'canceled']),
                ]
                existing_domain = [
                    ('membership_id', '=', product.id),
                    ('network_id', '=', network.id),
                    ('date_to', '>=', product.membership_date_to),
                    ('state', 'not in', ['canceled']),
                ]
                self._renew_and_send(
                    network=network,
                    product=product,
                    expired_lines_domain=expired_lines_domain,
                    existing_domain=existing_domain,
                    context_vals={
                        'membership_network_id': network.id,
                        'membership_join_date': product.membership_date_from,
                    },
                )

        rolling_products = self.env['product.product'].search([
            ('membership', '=', True),
            ('is_rolling', '=', True),
        ])
        for product in rolling_products:
            networks = self.filtered(lambda n: product in n.product_ids)
            for network in networks:
                expired_lines_domain = [
                    ('membership_id', '=', product.id),
                    ('network_id', '=', network.id),
                    ('date_to', '<', today),
                    ('state', 'in', ['old', 'canceled']),
                ]
                existing_domain = [
                    ('membership_id', '=', product.id),
                    ('network_id', '=', network.id),
                    ('date_to', '>=', today),
                    ('state', 'not in', ['canceled']),
                ]
                self._renew_and_send(
                    network=network,
                    product=product,
                    expired_lines_domain=expired_lines_domain,
                    existing_domain=existing_domain,
                    context_vals={
                        'membership_network_id': network.id,
                    },
                )

        return True

    def _renew_and_send(self, network, product, expired_lines_domain, existing_domain, context_vals):
        """Find expired partners, create renewal invoices, and send if configured."""
        expired_lines = self.env['membership.membership_line'].search(expired_lines_domain)
        partners_to_renew = expired_lines.mapped('partner').filtered(
            lambda p: not p.free_member and not self.env['membership.membership_line'].search_count([
                ('partner', '=', p.id),
                *existing_domain,
            ])
        )
        if not partners_to_renew:
            return

        invoices = partners_to_renew.with_context(**context_vals).create_membership_invoice(
            product=product,
            amount=product.list_price,
        )

        if network.send_invoices_automatically:
            invoices.action_post()
            membership_lines = self.env['membership.membership_line'].search([
                ('account_invoice_id', 'in', invoices.ids),
                ('network_id', '=', network.id),
            ])
            if membership_lines:
                membership_lines._send_invoice_automatically()