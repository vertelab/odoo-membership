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
    # def _compute_members(self):
    #     for network in self:
    #         if network.product_ids:
    #             # Get all membership lines for this product
    #             member_lines = self.env['membership.membership_line'].search([
    #                 ('membership_id', 'in', network.product_ids.ids)
    #             ])
    #             network.member_ids = member_lines.mapped('partner')
    #         else:
    #             network.member_ids = self.env['res.partner']

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
                'search_default_state': 1,
            },
        }

    def action_cron_renew_memberships(self):
        """
        Cron job and server action to renew static memberships.
        """
        today = date.today()
        # Look for all products that are memberships, NOT rolling, and have a future date range.
        products = self.env['product.product'].search([
            ('membership', '=', True),
            ('is_rolling', '=', False),
            ('membership_date_to', '>=', today),
        ])
        
        for product in products:
            networks = self.search([('product_ids', 'in', product.id)])
            for network in networks:
                # Find expired lines where the end date is BEFORE the product's new end date
                expired_lines = self.env['membership.membership_line'].search([
                    ('membership_id', '=', product.id),
                    ('network_id', '=', network.id),
                    ('date_to', '<', product.membership_date_to),
                    ('state', 'in', ['old', 'canceled']),
                ])
                
                # Filter to only those partners who DON'T have any current or future line for this product+network
                partners_to_renew = expired_lines.mapped('partner').filtered(
                    lambda p: not p.free_member and not self.env['membership.membership_line'].search_count([
                        ('partner', '=', p.id),
                        ('membership_id', '=', product.id),
                        ('network_id', '=', network.id),
                        ('date_to', '>=', product.membership_date_to),
                        ('state', 'not in', ['canceled']),
                    ])
                )

                if partners_to_renew:
                    partners_to_renew.with_context(
                        membership_network_id=network.id,
                        membership_join_date=product.membership_date_from,
                    ).create_membership_invoice(
                        product=product,
                        amount=product.list_price
                    )
        return True