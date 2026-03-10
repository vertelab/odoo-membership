from odoo import models, fields, api

class MembershipLine(models.Model):
    _inherit = 'membership.membership_line'

    network_id = fields.Many2one('membership.network', string='Network')

    @api.depends(
        'account_invoice_id.state',
        'account_invoice_id.amount_residual',
        'account_invoice_id.payment_state',
    )
    def _compute_state(self):
        # Filter only lines that have an invoice to avoid empty IN () SQL error
        lines_with_invoice = self.filtered('account_invoice_id')
        lines_without_invoice = self - lines_with_invoice

        # Handle lines without invoice (free members created directly)
        for line in lines_without_invoice:
            line.state = 'free' if not line.account_invoice_line else 'none'

        # Let Odoo handle the rest normally
        if lines_with_invoice:
            super(MembershipLine, lines_with_invoice)._compute_state()
