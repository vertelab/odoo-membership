from odoo import models, fields, api, _
from datetime import datetime
import logging

_logger = logging.getLogger(__name__)

class AccountInvoice(models.Model):
    _inherit = "account.invoice"
    current_year = datetime.now().year
    membership_date_start = fields.Date(string = "Membership Date Start",default=datetime.now().strftime('%Y-04-01'))
    membership_date_end = fields.Date(string = "Membership Date End",default=datetime.now().strftime('%s-03-31' %(current_year + 1)) )
    total_days = fields.Integer(string = "Total Mebership Days", compute='_get_membership_days', readonly=True)

    @api.multi
    @api.onchange('invoice.partner_id.date_start','invoice.partner_id.date_end')
    def _get_membership_days(self):
        for invoice in self:
            if invoice.partner_id.date_start:
                if invoice.partner_id.date_start > invoice.membership_date_start:
                    invoice.total_days = ((invoice.membership_date_end - invoice.partner_id.date_start).days + 1) /365 * 360 
                    if invoice.total_days >= 360:
                        raise Warning('It is longer than one year, please doubble check the join date for client %s ' %invoice.partner_id.name)
            elif invoice.partner_id.date_end:
                if invoice.partner_id.date_end < invoice.membership_date_end:
                    invoice.total_days = ((invoice.membership_date_end - invoice.partner_id.date_end).days + 1) /365 * 360 - 30
                    if invoice.total_days < 30:
                        raise Warning('Days left is less than 30 days, you do not need to create credit invoice for client %s ' %invoice.partner_id.name)
                
class AccountInvoiceLine(models.Model):
    _inherit = "account.invoice.line"

    @api.multi
    @api.onchange('invoice_id.price_unit','inovice_id.price_subtotal')
    def _get_price_on_days(self):
        if self.commercial_partner_id.date_start or self.commercial_partner_id.date_end:
            for invoice_line in self:
                if invoice_line.total_days != 0:
                    for line in self:
                        line.price_unit = line.product_id.lst_price / 360 * invoice_line.total_days
                        line.price_subtotal = line.price_unit * line.quantity
                else:
                    for line in self:
                        line.price_unit = line.product_id.lst_price 
                        line.price_subtotal = line.price_unit * line.quantity
