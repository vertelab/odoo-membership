from odoo import api, fields, models, tools

class MembershipNetwork(models.Model):
    _name = 'membership.network'
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