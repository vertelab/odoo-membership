from odoo import models, fields, api, _
from datetime import datetime
import logging

_logger = logging.getLogger(__name__)

class AccountInvoice(models.Model):
    _inherit = "account.invoice"

    total_days = fields.Integer(string = "Total Insurance Days", compute='_check_dates_insurance', readonly=True)

    def days_between(self, date_from, date_to):
        days = (date_to - date_from).days
        
        if days <= 0:
            days += 365
        elif days < 30:
            raise Warning('ERROR: Days left is less than 30 days. You cannot create credit invoice for client')
        elif days > 365:
            raise Warning('ERROR: Period is longer than one year. Please check the join date for client')
        
        DAYS_IN_YEAR = 360
        days *= round(DAYS_IN_YEAR / 365)
        
        return days

    @api.one
    @api.onchange('partner_id')
    def _check_dates_insurance(self):
        _logger.warn("~ Haze: in _check_dates_insurance ...")
        if self.partner_id:
            _logger.warn("~ Haze: looping through self.invoice_line_ids")
            for line in self.invoice_line_ids:
                _logger.warn("~ Haze: is this line an insurance product?")
                if line.product_id.insurance:
                    _logger.warn("~ Haze: YES! calculating insurance price ...")
                    
                    insurance_start = line.product_id.product_tmpl_id.insurance_date_from
                    insurance_end = line.product_id.product_tmpl_id.insurance_date_to
                    partner_start = self.partner_id.date_start
                    partner_end = self.partner_id.date_end
                    
                    line.total_days = self.days_between(partner_start or insurance_start, partner_end or insurance_end)
                    _logger.warn("~ Haze: total days was calculated to %s" % line.total_days)
                    
                    line.price = line.product_id.lst_price * line.total_days
                    line.price_subtotal = line.price_unit * line.quantity

class AccountInvoiceLine(models.Model):
    _inherit = "account.invoice.line"
    
    @api.one
    @api.onchange('product_id')
    def _check_dates_insurance(self):
        self.invoice_id._check_dates_insurance()
