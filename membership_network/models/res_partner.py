import random
from odoo import models, fields, api

class ResPartner(models.Model):
    _inherit = 'res.partner'

    company_type = fields.Selection(
        selection_add=[('network', 'Network')],
        store=True,
        compute='_compute_company_type',
        inverse='_write_company_type',
    )

    @api.depends('is_company')
    def _compute_company_type(self):
        for partner in self:
            # Only compute if not network - never overwrite network
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


    def _compute_table_history(self):
        for rec in self:
            rec.table_history_count = self.env['event.booking.table.history'].search_count([
                ('partner_ids', 'in', rec.id)
            ])

    table_history_count = fields.Integer(string="Table History Count", compute='_compute_table_history')
    is_network = fields.Boolean(string="Is Network")
    network_ids = fields.Many2many('membership.network', string="Network")

    def action_view_table_history(self):
        return {
            'name': 'Table History',
            'type': 'ir.actions.act_window',
            'res_model': 'event.booking.table.history',
            'view_mode': 'list,form',
            'target': 'current',
            'domain': [("partner_ids", 'in', self.id)]
        }

    # def action_create_network(self):
    #     vals = {
    #         'name': self.name,
    #         'network_partner_id': self.id,
    #     }
    #     network_id = self.env['membership.network'].create(vals)
    #     self.network_id = network_id.id

    def _server_action_join_membership(self):
        for partner in self:
            if not partner.network_ids:
                continue

            for network in partner.network_ids:
                if not network.product_ids:
                    continue

                product = random.choice(network.product_ids)

                existing = self.env['membership.membership_line'].search([
                    ('partner', '=', partner.id),
                    ('network_id', '=', network.id),
                    ('state', 'in', ['paid', 'invoiced', 'waiting', 'free']),
                ], limit=1)
                if existing:
                    continue

                invoice = partner.create_membership_invoice(
                    product=product,
                    amount=partner.membership_amount or product.list_price,
                )
                invoice.action_post()

                membership_line = self.env['membership.membership_line'].search([
                    ('partner', '=', partner.id),
                    ('membership_id', '=', product.id),
                    ('network_id', '=', False),
                ], order='id desc', limit=1)

                if membership_line:
                    membership_line.write({
                        'network_id': network.id,
                        # 'date_from': fields.Date.today(),
                        # 'date_to': fields.Date.today().replace(year=fields.Date.today().year + 1),
                    })
                