from odoo import models, fields, api

class Partner(models.Model):
    _inherit = 'res.partner'

    def _compute_table_history(self):
        for rec in self:
            rec.table_history_count = self.env['event.booking.table.history'].search_count([
                ('partner_ids', 'in', rec.id)
            ])

    table_history_count = fields.Integer(string="Table History Count", compute='_compute_table_history')
    is_network = fields.Boolean(string="Is Network")
    network_id = fields.Many2one('membership.network', string="Network")

    def action_view_table_history(self):
        return {
            'name': 'Table History',
            'type': 'ir.actions.act_window',
            'res_model': 'event.booking.table.history',
            'view_mode': 'list,form',
            'target': 'current',
            'domain': [("partner_ids", 'in', self.id)]
        }

    def action_create_network(self):
        vals = {
            'name': self.name,
            'network_partner_id': self.id,
        }
        network_id = self.env['membership.network'].create(vals)
        self.network_id = network_id.id
