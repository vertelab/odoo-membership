import re
from odoo import api, fields, models, _

class CreateTablesWizard(models.TransientModel):
    _name = 'event.booking.table.wizard'
    _description = 'Create Booking Tables Wizard'

    number_of_tables = fields.Integer(string='Number of Tables', default=1, required=True)
    capacity = fields.Integer(string='Capacity per Table', default=1, required=True)
    prefix = fields.Char(string='Table Prefix', default='Table')

    def action_create_tables(self):
        existing = self.env['event.booking.table'].search([
            ('name', 'ilike', self.prefix)
        ])

        numbers = []
        for table in existing:
            match = re.search(r'(\d+)$', table.name)
            if match:
                numbers.append(int(match.group(1)))
        start = max(numbers) + 1 if numbers else 1

        tables = []
        for i in range(self.number_of_tables):
            number = start + i
            tables.append({
                'name': f"{self.prefix} {number}",
                'capacity': self.capacity,
                'code': str(number),
            })
        self.env['event.booking.table'].create(tables)

        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('Tables Created'),
                'message': _('%s tables created successfully.') % self.number_of_tables,
                'type': 'success',
                'sticky': False,
            }
        }