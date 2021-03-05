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

    @api.onchange('partner_id','price_unit','price_subtotal')
    def _check_dates_insurance(self):
        _logger.warn("~ Haze: in _check_dates_insurance")
        
        if self.partner_id:
            _logger.warn("~ Haze: looping through self.invoice_line_ids %s " % self.invoice_line_ids)
            for line in self.invoice_line_ids:
                _logger.warn("~ Haze: this is an insurance product: %s" % line.product_id.insurance)
                
                if line.product_id.insurance:
                    insurance_start = line.product_id.product_tmpl_id.insurance_date_from
                    insurance_end = line.product_id.product_tmpl_id.insurance_date_to
                    partner_start = self.partner_id.date_start
                    partner_end = self.partner_id.date_end
                    
                    line.total_days = self.days_between(partner_start or insurance_start, partner_end or insurance_end)
                    _logger.warn("~ Haze1: total days was calculated to %s" % line.total_days)
                    line.price_unit = line.product_id.lst_price / 360 * line.total_days
                    # ~ _logger.warn('Haze1 price %s' %line.price_unit)
                    line.price_subtotal = line.price_unit * line.quantity
                    # ~ _logger.warn('Haze1 price sub %s' %line.price_subtotal)
                    vals = { 'price_unit': line.price_unit,
                             'price_subtotal': line.price_subtotal,
                     }
                    line.sudo().write(vals)
                    _logger.warn('Haze1 vals %s' %vals)
            # ~ self._onchange_eval('invoice_line_ids', "1", {})
        _logger.warn("~ Haze: _check_dates_insurance DONE")

class AccountInvoiceLine(models.Model):
    _inherit = "account.invoice.line"
    
   
    @api.onchange('product_id','price_unit','price_subtotal')
    
    def _check_dates_insurance_line(self):
        _logger.warn("~ Haze2: in _check_dates_insurance self.product_id%s" % self.product_id)
        _logger.warn("~ Haze2: in _check_dates_insurance 2 self.product_id.price_unit %s" % self.product_id.lst_price)
        # ~ _logger.warn("~ Haze: in _check_dates_insurance 2 self.product_id %s.price_subtotal" % self.product_)
        self.invoice_id._check_dates_insurance()
