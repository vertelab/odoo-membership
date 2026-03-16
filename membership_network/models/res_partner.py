import logging
import random
from odoo import models, fields, api, _

_logger = logging.getLogger(__name__)

MAX_SESSIONS = 3


class ResPartner(models.Model):
    _inherit = 'res.partner'

    company_type = fields.Selection(
        selection_add=[('network', 'Network')],
        store=True,
        compute='_compute_company_type',
        inverse='_write_company_type',
    )
    is_network = fields.Boolean(string="Is Network")
    network_ids = fields.Many2many(
        'membership.network',
        compute='_compute_network_ids',
        search='_search_network_ids',
        string='Networks',
    )
    people_met_count = fields.Integer(string="People Met", compute='_compute_people_met')

    @api.depends('member_lines.network_id', 'member_lines.state')
    def _compute_network_ids(self):
        for partner in self:
            active_lines = partner.member_lines.filtered(
                lambda l: l.state in ['paid', 'invoiced'] and l.network_id
            )
            partner.network_ids = active_lines.mapped('network_id')

    def _search_network_ids(self, operator, value):
        if operator in ('in', 'not in') and not isinstance(value, (list, tuple)):
            value = [value]
        
        partners = self.env['membership.membership_line'].search([
            ('network_id', operator, value),
            ('state', 'in', ['paid', 'invoiced']),
        ]).mapped('partner')
        return [('id', 'in', partners.ids)]
            

    @api.depends('is_company')
    def _compute_company_type(self):
        for partner in self:
            if partner.company_type == 'network':
                continue
            partner.company_type = 'company' if partner.is_company else 'person'

    def _write_company_type(self):
        for partner in self:
            if partner.company_type == 'network':
                continue
            partner.is_company = partner.company_type == 'company'

    @api.onchange('company_type')
    def onchange_company_type(self):
        if self.company_type == 'network':
            return
        self.is_company = (self.company_type == 'company')

    def _get_people_met(self):
        self.ensure_one()
        met_ids = set()

        past_regs = self.env['event.registration'].search([
            ('partner_id', '=', self.id),
            ('state', '=', 'done'),
        ])

        for reg in past_regs:
            for session in range(1, MAX_SESSIONS + 1):
                table = getattr(reg, f'session_{session}_table_id', None)
                if not table:
                    continue
                same_table = self.env['event.registration'].search([
                    ('event_id', '=', reg.event_id.id),
                    ('state', '=', 'done'),
                    ('partner_id', '!=', self.id),
                    (f'session_{session}_table_id', '=', table.id),
                ])
                met_ids.update(same_table.mapped('partner_id').ids)

        return self.env['res.partner'].browse(met_ids)

    def _compute_people_met(self):
        for partner in self:
            partner.people_met_count = len(partner._get_people_met())

    # def action_view_people_met(self):
    #     self.ensure_one()
    #     people_met = self._get_people_met()
    #     return {
    #         'name': 'People Met',
    #         'type': 'ir.actions.act_window',
    #         'res_model': 'res.partner',
    #         'view_mode': 'list,form',
    #         'domain': [('id', 'in', people_met.ids)],
    #     }

    def action_view_people_met(self):
        self.ensure_one()
        met_registration_ids = []

        past_regs = self.env['event.registration'].search([
            ('partner_id', '=', self.id),
            ('state', '=', 'done'),
        ])

        for reg in past_regs:
            for session in range(1, MAX_SESSIONS + 1):
                table = getattr(reg, f'session_{session}_table_id', None)
                if not table:
                    continue
                same_table = self.env['event.registration'].search([
                    ('event_id', '=', reg.event_id.id),
                    ('state', '=', 'done'),
                    ('partner_id', '!=', self.id),
                    (f'session_{session}_table_id', '=', table.id),
                ])
                met_registration_ids.extend(same_table.ids)

        return {
            'name': 'People Met',
            'type': 'ir.actions.act_window',
            'res_model': 'event.registration',
            'view_mode': 'list,form',
            'domain': [('id', 'in', met_registration_ids)],
            'context': {
                'create': False,
                'search_default_group_event': 1,
            },
        }

    # def _server_action_join_membership(self):
    #     for partner in self:
    #         if not partner.network_ids:
    #             continue

    #         for network in partner.network_ids:
    #             if not network.product_ids:
    #                 continue

    #             product = random.choice(network.product_ids)

    #             existing = self.env['membership.membership_line'].search([
    #                 ('partner', '=', partner.id),
    #                 ('network_id', '=', network.id),
    #                 ('state', 'in', ['paid', 'invoiced', 'waiting', 'free']),
    #             ], limit=1)
    #             if existing:
    #                 continue

    #             invoice = partner.create_membership_invoice(
    #                 product=product,
    #                 amount=partner.membership_amount or product.list_price,
    #             )
    #             invoice.action_post()

    #             membership_line = self.env['membership.membership_line'].search([
    #                 ('partner', '=', partner.id),
    #                 ('membership_id', '=', product.id),
    #                 ('network_id', '=', False),
    #             ], order='id desc', limit=1)

    #             if membership_line:
    #                 membership_line.write({'network_id': network.id})

    def _server_action_join_membership(self):
        return {
            'name': _('Buy Membership'),
            'type': 'ir.actions.act_window',
            'res_model': 'membership.invoice',
            'view_mode': 'form',
            'view_id': self.env.ref('membership.view_membership_invoice_view').id,
            'target': 'new',
            'context': {
                'active_ids': self.ids,
                'active_model': 'res.partner',
            }
        }

    # def _migrate_membership_line_networks(self):
    #     """One-time backfill: set network_id on existing membership lines that have none."""
    #     lines = self.env['membership.membership_line'].search([
    #         ('network_id', '=', False),
    #         ('membership_id', '!=', False),
    #     ])
    #     for line in lines:
    #         network = self.env['membership.network'].search([
    #             ('product_ids', 'in', line.membership_id.id)
    #         ], limit=1)
    #         if network:
    #             line.network_id = network.id

    def create_membership_invoice(self, product, amount):
        """Override to pass join_date and associate_member context into membership line creation."""
        invoice_vals_list = []
        for partner in self:
            addr = partner.address_get(['invoice'])
            if partner.free_member:
                from odoo.exceptions import UserError
                raise UserError(_("Partner is a free Member."))
            if not addr.get('invoice', False):
                from odoo.exceptions import UserError
                raise UserError(_("Partner doesn't have an address to make the invoice."))
            invoice_vals_list.append({
                'move_type': 'out_invoice',
                'partner_id': partner.id,
                'invoice_line_ids': [(0, None, {
                    'product_id': product.id,
                    'quantity': 1,
                    'price_unit': amount,
                    'tax_ids': [(6, 0, product.taxes_id.filtered_domain(
                        self.env['account.tax']._check_company_domain(self.env.company)
                    ).ids)]
                })]
            })
        return self.env['account.move'].with_context(
            membership_join_date=self.env.context.get('membership_join_date'),
            membership_associate_member_id=self.env.context.get('membership_associate_member_id'),
            membership_network_id=self.env.context.get('membership_network_id'),
        ).create(invoice_vals_list)