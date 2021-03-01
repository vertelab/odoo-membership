from odoo import models, fields, api, _
from datetime import datetime
import logging

_logger = logging.getLogger(__name__)

class AccountInvoice(models.Model):
    _inherit = "account.invoice"
    # ~ current_year = datetime.now().year
    # ~ insurance_date_start = fields.Date(string = "Insurance Date Start",default=datetime.now().strftime('%Y-04-01'))
    # ~ insurance_date_end = fields.Date(string = "Insurance Date End",default=datetime.now().strftime('%s-03-31' %(current_year + 1)) )
    total_days = fields.Integer(string = "Total Insurance Days", compute='_check_dates_insurance', readonly=True)
    # ~ insurance_price_unit = fields.Float(compute='_check_dates_insurance')
    # ~ insurance_price_subtotal =fields.Float(compute='_check_dates_insurance')
    

    @api.one
    @api.onchange('partner_id')
    def _check_dates_insurance(self):
        if self.partner_id:
            for line in self.invoice_line_ids:
                if line.product_id.insurance:
                    if self.partner_id.date_start > line.product_id.product_tmpl_id.insurance_date_from:
                        line.total_days = ((line.product_id.product_tmpl_id.insurance_date_to - self.partner_id.date_start).days + 1) /365 * 360
                        line.price = line.product_id.lst_price / 360 * line.total_days
                        line.price_subtotal = line.price_unit * line.quantity
                        # ~ raise Warning(line.total_days)
                        # ~ if line.total_days >= 365:
                            # ~ raise Warning('It is longer than one year, please doubble check the join date for client %s ' %self.partner_id.name) 
                    elif self.partner_id.date_end < line.product_id.product_tmpl_id.insurance_date_to:
                        line.total_days = ((line.product_id.product_tmpl_id.insurance_date_to - self.partner_id.date_end).days + 1) /365 * 360 - 30
                        if line.total_days > 30 and line.total_days < 365:
                            line.price = line.product_id.lst_price / 360 * line.total_days
                            line.price_subtotal = line.price_unit * line.quantity
                        else:
                            line.price_unit = line.product_id.lst_price 
                            line.price_subtotal = line.price_unit * line.quantity
                            
                        if line.total_days <= 30:
                            raise Warning('Days left is less than 30 days, you do not need to create credit invoice for client %s ' %invoice.partner_id.name)
                        

class AccountInvoiceLine(models.Model):
    _inherit = "account.invoice.line"
    # ~ total_days = fields.Integer(related="invoice_id.total_days")
    # ~ total_days = fields.Integer(string = "Total Insurance Days", compute='_check_dates_insurance', readonly=True)
    # ~ price_unit = fields.Float(compute='_get_price_on_days')
    # ~ price_subtotal =fields.Float(compute='_get_price_on_days')
    # ~ @api.multi
    # ~ @api.onchange('price_unit','price_subtotal')
    # ~ def _get_price_on_days(self):
        # ~ if self.partner_id.date_start or self.partner_id.date_end:
            # ~ for invoice_line in self:
                # ~ if invoice_line.total_days != 0:
                    # ~ for line in self:
                        # ~ line.price_unit = line.product_id.lst_price / 360 * invoice_line.total_days
                        # ~ line.price_subtotal = line.price_unit * line.quantity
                # ~ else:
                    # ~ for line in self:
                        # ~ line.price_unit = line.product_id.lst_price 
                        # ~ line.price_subtotal = line.price_unit * line.quantity

    @api.one
    @api.onchange('product_id')
    def _check_dates_insurance(self):
        self.invoice_id._check_dates_insurance()
