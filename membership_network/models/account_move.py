# models/account.py
import logging
from odoo import api, fields, models
from datetime import date
from dateutil.relativedelta import relativedelta

_logger = logging.getLogger(__name__)


def _compute_membership_dates(line, join_date=None):
    product = line.product_id
    template = product.product_tmpl_id

    if template.is_rolling:
        effective_start = join_date or line.move_id.invoice_date or date.today()
        unit = template.membership_duration_unit or 'years'
        duration = template.membership_duration or 1
        delta = relativedelta(**{unit: duration})
        return effective_start, effective_start + delta

    date_from = product.membership_date_from
    date_to = product.membership_date_to
    invoice_date = line.move_id.invoice_date or date.min
    if date_from and date_from < invoice_date < (date_to or date.min):
        date_from = invoice_date
    return date_from, date_to


class AccountMove(models.Model):
    _inherit = 'account.move'

    def button_draft(self):
        res = super().button_draft()
        for move in self:
            if move.move_type == 'out_invoice':
                self.env['membership.membership_line'].search([
                    ('account_invoice_line', 'in', move.mapped('invoice_line_ids').ids)
                ]).write({'date_cancel': False})
        return res

    def button_cancel(self):
        res = super().button_cancel()
        for move in self:
            if move.move_type == 'out_invoice':
                self.env['membership.membership_line'].search([
                    ('account_invoice_line', 'in', move.mapped('invoice_line_ids').ids)
                ]).write({'date_cancel': fields.Date.today()})
        return res

    def write(self, vals):
        res = super().write(vals)
        if 'partner_id' in vals:
            self.env['membership.membership_line'].search([
                ('account_invoice_line', 'in', self.mapped('invoice_line_ids').ids)
            ]).write({'partner': vals['partner_id']})
        return res


class AccountMoveLine(models.Model):
    _inherit = 'account.move.line'

    def _get_membership_join_date(self):
        join_date = self.env.context.get('membership_join_date')
        if isinstance(join_date, str):
            return fields.Date.from_string(join_date)
        return join_date

    def _get_membership_associate_member_id(self):
        return self.env.context.get('membership_associate_member_id')

    def _get_membership_network_id(self):
        return self.env.context.get('membership_network_id')

    def _fix_membership_lines(self, lines):
        """
        After super() creates membership lines with default Odoo logic,
        update them with:
        - correct rolling or static dates
        - join_date
        - associate_member_id
        - network_id
        All values come from context set by the wizard.
        """
        join_date = self._get_membership_join_date()
        associate_member_id = self._get_membership_associate_member_id()
        network_id = self._get_membership_network_id()

        to_process = lines.filtered(
            lambda l: l.move_id.move_type == 'out_invoice' and l.product_id.membership
        )
        if not to_process:
            return

        membership_lines = self.env['membership.membership_line'].search([
            ('account_invoice_line', 'in', to_process.ids)
        ])

        for ml in membership_lines:
            date_from, date_to = _compute_membership_dates(ml.account_invoice_line, join_date)
            vals = {
                'date_from': date_from,
                'date_to': date_to,
            }
            if join_date:
                vals['date'] = join_date
            if associate_member_id:
                vals['associate_member_id'] = associate_member_id
            if network_id:
                vals['network_id'] = network_id
            ml.write(vals)

    def write(self, vals):
        res = super().write(vals)
        self._fix_membership_lines(self)
        return res

    @api.model_create_multi
    def create(self, vals_list):
        lines = super().create(vals_list)
        self._fix_membership_lines(lines)
        return lines