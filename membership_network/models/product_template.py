# models/product.py
from odoo import fields, models

DURATION_UNIT = [
    ('days', 'Day(s)'),
    ('weeks', 'Week(s)'),
    ('months', 'Month(s)'),
    ('years', 'Year(s)'),
]

class ProductTemplate(models.Model):
    _inherit = 'product.template'

    is_rolling = fields.Boolean(
        string='Rolling Membership',
        help='If checked, membership duration is calculated from the join date. '
             'Otherwise, fixed start/end dates from the product are used.'
    )
    membership_duration = fields.Integer(
        string='Duration',
        default=1,
        help='Duration of the membership for rolling memberships.'
    )
    membership_duration_unit = fields.Selection(
        selection=DURATION_UNIT,
        string='Unit',
        default='years',
        help='Unit of duration for rolling memberships.'
    )