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

    # def _fix_membership_lines(self, lines):
    #     """
    #     Ensures membership lines exist for membership products and updates them.
    #     """
    #     join_date = self._get_membership_join_date()
    #     associate_member_id = self._get_membership_associate_member_id()
    #     network_id = self._get_membership_network_id()

    #     to_process = lines.filtered(
    #         lambda l: l.move_id.move_type == 'out_invoice' and l.product_id.membership
    #     )
    #     if not to_process:
    #         return

    #     for line in to_process:
    #         ml = self.env['membership.membership_line'].search([
    #             ('account_invoice_line', '=', line.id)
    #         ], limit=1)
            
    #         date_from, date_to = _compute_membership_dates(line, join_date)
    #         vals = {
    #             'partner': line.move_id.partner_id.id,
    #             'membership_id': line.product_id.id,
    #             'member_price': line.price_unit,
    #             'date_from': date_from,
    #             'date_to': date_to,
    #             'account_invoice_line': line.id,
    #         }
    #         if join_date:
    #             vals['date'] = join_date
    #         if associate_member_id:
    #             vals['associate_member_id'] = associate_member_id
    #         if network_id:
    #             vals['network_id'] = network_id
            
    #         if ml:
    #             ml.write(vals)
    #         else:
    #             self.env['membership.membership_line'].create(vals)

    #         # Post and Send invoice automatically if network settings allow it
    #         if network_id:
    #             network = self.env['membership.network'].browse(network_id)
    #             if network.send_invoices_automatically:
    #                 move = line.move_id
    #                 if move.state == 'draft':
    #                     move.action_post()
    #                 # Trigger the send action (non-blocking if possible)
    #                 move.action_invoice_sent()

    # def write(self, vals):
    #     res = super().write(vals)
    #     self._fix_membership_lines(self)
    #     return res

    # @api.model_create_multi
    # def create(self, vals_list):
    #     lines = super().create(vals_list)
    #     self._fix_membership_lines(lines)
    #     return lines
