from odoo import models, fields, api, _

from datetime import datetime
import logging

_logger = logging.getLogger(__name__)
DAYS_IN_YEAR = 360


class AccountInvoiceLine(models.Model):
    _inherit = "account.invoice.line"
    
    total_days = fields.Integer(string = "Total Insurance Days",
                                compute='_check_dates_insurance',
                                readonly=True)
                                
    @api.one
    def _check_dates_insurance(self):
        if self.product_id and self.product_id.insurance:
            insurance_start = self.product_id.product_tmpl_id.insurance_date_from
            insurance_end = self.product_id.product_tmpl_id.insurance_date_to
            partner_start = self.partner_id.date_start
            partner_end = self.partner_id.date_end

            self.total_days = self.days_between(partner_start or insurance_start,
                                                partner_end or insurance_end)


    def days_between(self, date_from, date_to):
        days = (date_to - date_from).days

        if days <= 0:
            days += 365
        elif days < 30:
            raise Warning('ERROR: Days left is less than 30 days. You cannot '
                          'create credit invoice for client')
        elif days > 365:
            raise Warning('ERROR: Period is longer than one year. '
                          'Please check the join date for client')

        days *= round(DAYS_IN_YEAR / 365)

        return days

    @api.one
    def X_compute_price(self):
        super(AccountInvoiceLine, self)._compute_price()
        if self.product_id and self.product_id.insurance:
            self.price_unit = (self.product_id.lst_price /
                               DAYS_IN_YEAR *
                               self.total_days)
            self.price_subtotal = self.price_unit * self.quantity
