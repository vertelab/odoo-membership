from odoo import api, fields, models, tools

class MembershipNetwork(models.Model):
    _name = 'membership.network'
    _description = 'Membership Network'

    name = fields.Char(string='Name', required=True)
    description = fields.Text(string='Description')
    product_id = fields.Many2one('product.product', string='Membership Product',
        domain=[('membership', '=', True)],
        help='Membership product for this network. Partners who purchase this product become members.')
    member_ids = fields.Many2many('res.partner', compute='_compute_members', string='Members', store=False)
    member_count = fields.Integer(compute='_compute_member_count', string='Number of Members')
    active_member_count = fields.Integer(compute='_compute_member_count', string='Active Members')

    def _compute_members(self):
        for network in self:
            if network.product_id:
                # Get all membership lines for this product
                member_lines = self.env['membership.membership_line'].search([
                    ('membership_id', '=', network.product_id.id)
                ])
                network.member_ids = member_lines.mapped('partner')
            else:
                network.member_ids = self.env['res.partner']

    @api.depends('member_ids')
    def _compute_member_count(self):
        for network in self:
            network.member_count = len(network.member_ids)
            # Count active members (paid, invoiced, or free)
            active_count = 0
            for partner in network.member_ids:
                if partner.membership_state in ['paid', 'invoiced', 'free']:
                    active_count += 1
            network.active_member_count = active_count
