# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

import datetime
import logging

from odoo import api, fields, models, _
from . import insurance
from odoo.addons import decimal_precision as dp
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)

STATE = [
    ('none', 'Non Insurance'),
    ('canceled', 'Cancelled Insurance'),
    ('old', 'Old Insurance'),
    ('waiting', 'Waiting Insurance'),
    ('invoiced', 'Invoiced Insurance'),
    ('free', 'Free Insurance'),
    ('paid', 'Paid Insurance'),
]

DAYS_IN_YEAR = 360

class res_partner(models.Model):
    _inherit = 'res.partner'

    def set_associate_member(self):
        for partner in self.env['res.partner'].search([]):
            partner.associate_member = partner.parent_id

    """ This is code for finding contacts which has no city or email in the database, it is for serveraction because it is not working in the python which is strange :(
    bugs = env['res.partner'].search(['|',('email','=',False),('city','=',False)])
    res = env['ir.actions.act_window'].for_xml_id(
    'membership', 'action_membership_members')
    res['domain'] = "[('id','in',%s)]" % bugs.mapped('id')
    action = res"""

    # for insurance page
    associate_member = fields.Many2one('res.partner', string='Associate Member',
        help="A member with whom you want to associate your insurance."
             "It will consider the insurance state of the associated member.")

    insurance_lines = fields.One2many('insurance.insurance_line', 'partner', string='Insurance')

    insurance_amount = fields.Float(string='Insurance Amount', digits=(16, 2),
        help='The price negotiated by the partner')
    insurance_state = fields.Selection(insurance.STATE, compute='_compute_insurance_state',
        string='Current Insurance Status', store=True,
        help='It indicates the insurance state.\n'
             '-Non insurance: A partner who has not applied for any insurance.\n'
             '-Cancelled insurance: A insurance who has cancelled his insurance.\n'
             '-Old insurance: A insurance whose insurance date has expired.\n'
             '-Waiting insurance: A insurance who has applied for the insurance and whose invoice is going to be created.\n'
             '-Invoiced insurance: A insurance whose invoice has been created.\n'
             '-Paying insurance: A insurance who has paid the insurance fee.')
    insurance_start = fields.Date(compute='_compute_insurance_start',
        string ='Insurance Start Date',
        help="Date from which insurance becomes active.")
    insurance_stop = fields.Date(compute='_compute_insurance_stop',
        string ='Insurance End Date',
        help="Date until which insurance remains active.")
    insurance_cancel = fields.Date(compute='_compute_insurance_cancel',
        string ='Cancel insurance Date', store=True,
        help="Date on which insurance has been cancelled")

    @api.depends('insurance_lines.account_invoice_line.invoice_id.state',
                 'insurance_lines.account_invoice_line.invoice_id.invoice_line_ids',
                 'insurance_lines.account_invoice_line.invoice_id.payment_ids',
                 'insurance_lines.account_invoice_line.invoice_id.payment_move_line_ids',
                 'insurance_lines.account_invoice_line.invoice_id.partner_id',
                 'insurance_lines.date_to', 'insurance_lines.date_from',
                 'associate_member')
    def _compute_insurance_state(self):
        values = self._insurance_state()
        for partner in self:
            partner.insurance_state = values[partner.id]

        # Do not depend directly on "associate_member.insurance_state" or we might end up in an
        # infinite loop. Since we still need this dependency somehow, we explicitly search for the
        # "parent insurances" and trigger a recompute.
        parent_insurances = self.search([('associate_member', 'in', self.ids)]) - self
        if parent_insurances:
            parent_insurances._recompute_todo(self._fields['insurance_state'])

    @api.depends('insurance_lines.account_invoice_line.invoice_id.state',
                 'insurance_lines.account_invoice_line.invoice_id.invoice_line_ids',
                 'insurance_lines.account_invoice_line.invoice_id.payment_ids',
                 'insurance_lines.date_to', 'insurance_lines.date_from', 'insurance_lines.date_cancel',
                 'insurance_state',
                 'associate_member.insurance_state')
    def _compute_insurance_start(self):
        """Return  date of insurance"""
        for partner in self:
            partner.insurance_start = self.env['insurance.insurance_line'].search([
                ('partner', '=', partner.associate_member.id or partner.id), ('date_cancel','=',False)
            ], limit=1, order='date_from').date_from

    @api.depends('insurance_lines.account_invoice_line.invoice_id.state',
                 'insurance_lines.account_invoice_line.invoice_id.invoice_line_ids',
                 'insurance_lines.account_invoice_line.invoice_id.payment_ids',
                 'insurance_lines.date_to', 'insurance_lines.date_from', 'insurance_lines.date_cancel',
                 'insurance_state',
                 'associate_member.insurance_state')
    def _compute_insurance_stop(self):
        InsuranceLine = self.env['insurance.insurance_line']
        for partner in self:
            partner.insurance_stop = self.env['insurance.insurance_line'].search([
                ('partner', '=', partner.associate_member.id or partner.id),('date_cancel','=',False)
            ], limit=1, order='date_to desc').date_to

    @api.depends('insurance_lines.account_invoice_line.invoice_id.state',
                 'insurance_lines.account_invoice_line.invoice_id.invoice_line_ids',
                 'insurance_lines.account_invoice_line.invoice_id.payment_ids',
                 'insurance_lines.date_to', 'insurance_lines.date_from', 'insurance_lines.date_cancel',
                 'insurance_state',
                 'associate_member.insurance_state')
    def _compute_insurance_cancel(self):
        for partner in self:
            partner.insurance_cancel = self.env['insurance.insurance_line'].search([
                ('partner', '=', partner.id)
            ], limit=1, order='date_cancel desc').date_cancel

    def _insurance_state(self):
        """This Function return insurance State For Given Partner."""
        res = {}
        today = fields.Date.today()
        for partner in self:
            res[partner.id] = 'none'

            if partner.associate_member:
                res_state = partner.associate_member._insurance_state()
                res[partner.id] = res_state[partner.associate_member.id]
                continue

            s = 4
            if partner.insurance_lines:
                for mline in partner.insurance_lines.sorted(key=lambda r: r.id):
                    if (mline.date_to or date.min) >= today and (mline.date_from or date.min) <= today:
                        if mline.account_invoice_line.invoice_id.partner_id == partner:
                            mstate = mline.account_invoice_line.invoice_id.state
                            if mstate == 'paid':
                                inv = mline.account_invoice_line.invoice_id
                                for ml in inv.payment_move_line_ids:
                                    if any(ml.invoice_id.filtered(lambda inv: inv.type == 'out_refund')):
                                        s = 2
                                    else:
                                        s = 0
                            elif mstate == 'open' and s != 0:
                                s = 1
                            elif mstate == 'cancel' and s != 0 and s != 1:
                                s = 2
                            elif mstate == 'draft' and s != 0 and s != 1:
                                s = 3
                        """
                            If we have a line who is in the period and paid,
                            the line is valid and can be used for the insurance status.
                        """
                        if s == 0:
                            break
                    else:
                        if mline.account_invoice_line.invoice_id.partner_id == partner:
                            mstate = mline.account_invoice_line.invoice_id.state
                            if mstate == 'paid':
                                s = 5
                            else:
                                s = 6
                if s == 4:
                    for mline in partner.insurance_lines:
                        if (mline.date_from or date.min) < today and (mline.date_to or date.min) < today and (mline.date_from or date.min) <= (mline.date_to or date.min) and mline.account_invoice_line and mline.account_invoice_line.invoice_id.state == 'paid':
                            s = 5
                        else:
                            s = 6
                if s == 0:
                    res[partner.id] = 'paid'
                elif s == 1:
                    res[partner.id] = 'invoiced'
                elif s == 2:
                    res[partner.id] = 'canceled'
                elif s == 3:
                    res[partner.id] = 'waiting'
                elif s == 5:
                    res[partner.id] = 'old'
                elif s == 6:
                    res[partner.id] = 'none'
        return res

    @api.one
    @api.constrains('associate_member')
    def _check_recursion_associate_member(self):
        level = 100
        while self:
            self = self.associate_member
            if not level:
                raise ValidationError(_('You cannot create recursive associated members.'))
            level -= 1

    @api.model
    def _cron_update_insurance(self):
        partners = self.search([('insurance_state', 'in', ['invoiced', 'paid'])])
        # mark the field to be recomputed, and recompute it
        partners._recompute_todo(self._fields['insurance_state'])
        self.recompute()

    @api.multi
    def create_insurance_invoice(self, product_id=None, datas=None):
        """
        Create Customer Invoice of insurance for partners.
        @param datas: datas has dictionary value which consist Id of Insurance product and Cost Amount of Insurance.
                      datas = {'insurance_product_id': None, 'amount': None}
        """
        product_id = product_id or datas.get('insurance_product_id')
        amount = datas.get('amount', 0.0)
        invoice_list = []
        for partner in self:
            addr = partner.address_get(['invoice'])
            if not addr.get('invoice', False):
                raise UserError(_("Partner doesn't have an address to make the invoice."))
            if partner.date_end:
                invoice = self.env['account.invoice'].create({
                    'partner_id': partner.id,
                    'type': 'out_refund',
                    'account_id': partner.property_account_receivable_id.id,
                    'fiscal_position_id': partner.property_account_position_id.id
                })
            elif partner.date_start:
                invoice = self.env['account.invoice'].create({
                    'partner_id': partner.id,
                    'type': 'out_invoice',
                    'account_id': partner.property_account_receivable_id.id,
                    'fiscal_position_id': partner.property_account_position_id.id
                })
            else:
                invoice = self.env['account.invoice'].create({
                    'partner_id': partner.id,
                    'account_id': partner.property_account_receivable_id.id,
                    'fiscal_position_id': partner.property_account_position_id.id
                })
            line_values = {
                'product_id': product_id,
                'price_unit': amount,
                'invoice_id': invoice.id,
            }
            # create a record in cache, apply onchange then revert back to a dictionnary
            invoice_line = self.env['account.invoice.line'].new(line_values)
            invoice_line._onchange_product_id()
            line_values = invoice_line._convert_to_write({name: invoice_line[name] for name in invoice_line._cache})
            line_values['price_unit'] = amount
            invoice.write({'invoice_line_ids': [(0, 0, line_values)]})
            invoice_list.append(invoice)
            invoice.compute_taxes()

        # Add extra products
        for invoice in invoice_list:
            for line in invoice.invoice_line_ids:
                for insurance_product in line.product_id.insurance_product_ids:
                    # create a record in cache, apply onchange then revert back to a dictionnary
                    invoice_line = self.env['account.invoice.line'].new({'product_id': insurance_product.id,
                                                                         'price_unit': insurance_product.lst_price,
                                                                         'inovice_id':invoice.id})
                    invoice_line._onchange_product_id()
                    line_values = invoice_line._convert_to_write({name: invoice_line[name] for name in invoice_line._cache})
                    line_values['name'] = insurance_product.name
                    line_values['account_id'] = insurance_product.property_account_income_id.id if insurance_product.property_account_income_id else self.env['account.account'].search([('user_type_id','=',self.env.ref('account.data_account_type_revenue').id)])[0].id
                    invoice.write({'invoice_line_ids': [(0, 0, line_values)]})
        # Calculate amount and qty
        for invoice in invoice_list:
            for line in invoice.invoice_line_ids:
                if line.product_id.insurance_code:
                    line.price_unit, line.quantity = line.product_id.insurance_get_amount_qty(invoice.partner_id)
        return invoice_list


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
                 'account_invoice_line.invoice_id.payment_ids.invoice_ids.type',
                 'date_cancel')
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
            if not fetched or self.date_cancel:
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

    def button_cancel_insurance(self):
        view = self.env.ref('membership_insurance.view_insurance_cancel')
        ctx = {'default_line_id': self.id}
        return {
            'name': _('Cancel Insurance'),
            'type': 'ir.actions.act_window',
            'view_mode': 'form',
            'res_model': 'insurance.cancel_insurance',
            'views': [(view.id, 'form')],
            'view_id': view.id,
            'target': 'new',
            'context': ctx,
        }

class CancelInsurance(models.TransientModel):
    _name = 'insurance.cancel_insurance'
    _description = 'Cancel insurance and create refund invoice.'
    cancel_from_date = fields.Date(string='Cancel from', default=fields.Date.today)
    product_id = fields.Many2one(related='line_id.insurance_id', readonly=True)
    line_id = fields.Many2one('insurance.insurance_line', string='Insurance Line')
    refund_amount = fields.Float(string='Amount Refunded (ex taxes)', compute='_compute_refund')

    @api.multi
    def cancel_insurance(self):
        _logger.warning(f'lineid:{self.line_id}')
        journal_id = self.line_id.account_invoice_id.journal_id.id
        invoice = self.line_id.account_invoice_id.refund(self.cancel_from_date, self.cancel_from_date, 'Avbruten försäkring', journal_id)

        # Remove lines that are not refunded this time.
        invoice.invoice_line_ids.filtered(lambda r: r.product_id.id != self.product_id.id).unlink()

        # Calculate ratio to refund.
        ratio = self.refund_ratio(self.cancel_from_date, self.line_id.date_to)
        # Apply refund.
        for line in invoice.invoice_line_ids:
            line.price_unit = line.price_unit * ratio
            line._onchange_eval('price_unit', "1", {})
        invoice.compute_taxes()
        self.line_id.date_cancel = self.cancel_from_date

        result = self.env.ref('account.action_invoice_out_refund').read()[0]
        view_ref = self.env.ref('account.invoice_form')
        form_view = [(view_ref.id, 'form')]
        result['views'] = form_view
        result['res_id'] = invoice.id
        return result

    @api.depends('cancel_from_date')
    def _compute_refund(self):
        ratio = self.refund_ratio(self.cancel_from_date, self.line_id.date_to)
        line = self.line_id.account_invoice_line
        self.refund_amount = line.price_unit * line.quantity * ratio

    def refund_ratio(self, date_from, date_to):
        days = (date_to - date_from).days

        if days <= 0:
            days += 365
        elif days < 30:
            raise UserError('ERROR: Days left is less than 30 days. You cannot '
                          'create credit invoice for client')
        elif days > 365:
            raise UserError('ERROR: Period is longer than one year. '
                          'Please check the join date for client')

        return 1 - (days / DAYS_IN_YEAR)
