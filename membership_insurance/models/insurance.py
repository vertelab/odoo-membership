# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models
from odoo.addons import decimal_precision as dp

STATE = [
    ('none', 'Non Insurance'),
    ('canceled', 'Cancelled Insurance'),
    ('old', 'Old Insurance'),
    ('waiting', 'Waiting Insurance'),
    ('invoiced', 'Invoiced Insurance'),
    ('free', 'Free Insurance'),
    ('paid', 'Paid Insurance'),
]


class InsuranceLine(models.Model):
    _name = 'insurance.insurance_line'
    _rec_name = 'partner'
    _order = 'id desc'
    _description = 'Insurance Line'

    partner = fields.Many2one('res.partner', string='Partner', ondelete='cascade', index=True)
    insurance_id = fields.Many2one('product.product', string="Insurance", required=True)
    date_from = fields.Date(string='From', readonly=True)
    date_to = fields.Date(string='To', readonly=True)
    date_cancel = fields.Date(string='Cancel date')
    date = fields.Date(string='Join Date',
        help="Date on which Insurance has joined the Insurance")
    insurance_price = fields.Float(string='Insurance Fee',
        digits=dp.get_precision('Product Price'), required=True,
        help='Amount for the Insurance')
    account_invoice_line = fields.Many2one('account.invoice.line', string='Account Invoice line', readonly=True, ondelete='cascade')
    account_invoice_id = fields.Many2one('account.invoice', related='account_invoice_line.invoice_id', string='Invoice', readonly=True)
    company_id = fields.Many2one('res.company', related='account_invoice_line.invoice_id.company_id', string="Company", readonly=True, store=True)
    state = fields.Selection(STATE, compute='_compute_state', string='Insurance Status', store=True,
        help="It indicates the Insurance status.\n"
             "-Non Insurance: A Insurance who has not applied for any Insurance.\n"
             "-Cancelled Insurance: A Insurance who has cancelled his Insurance.\n"
             "-Old Insurance: A Insurance whose Insurance date has expired.\n"
             "-Waiting Insurance: A Insurance who has applied for the Insurance and whose invoice is going to be created.\n"
             "-Invoiced Insurance: A Insurance whose invoice has been created.\n"
             "-Paid Insurance: A Insurance who has paid the Insurance amount.")

    @api.depends('account_invoice_line.invoice_id.state',
                 'account_invoice_line.invoice_id.payment_ids',
                 'account_invoice_line.invoice_id.payment_ids.invoice_ids.type')
    def _compute_state(self):
        """Compute the state lines """
        Invoice = self.env['account.invoice']
        for line in self:
            self._cr.execute('''
            SELECT i.state, i.id FROM
            account_invoice i
            WHERE
            i.id = (
                SELECT l.invoice_id FROM
                account_invoice_line l WHERE
                l.id = (
                    SELECT  ml.account_invoice_line FROM
                    insurance_insurance_line ml WHERE
                    ml.id = %s
                    )
                )
            ''', (line.id,))
            fetched = self._cr.fetchone()
            if not fetched:
                line.state = 'canceled'
                continue
            istate = fetched[0]
            if istate == 'draft':
                line.state = 'waiting'
            elif istate == 'open':
                line.state = 'invoiced'
            elif istate == 'paid':
                line.state = 'paid'
                invoices = Invoice.browse(fetched[1]).payment_move_line_ids.mapped('invoice_id')
                if invoices.filtered(lambda invoice: invoice.type == 'out_refund'):
                    line.state = 'canceled'
            elif istate == 'cancel':
                line.state = 'canceled'
            else:
                line.state = 'none'
