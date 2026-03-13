# models/mailing.py
from odoo import fields, models


class MailingMailing(models.Model):
    _inherit = 'mailing.mailing'

    ref_id = fields.Reference(
        selection=[('event.event', 'Event')],
        string='Reference',
    )

    def _render_field(self, field, res_ids, engine='inline_template',
                      compute_lang=False, set_lang=False,
                      add_context=None, options=None):
        """Inject ref_id into render context so templates can use ${ref.field_name}."""
        if self.ref_id:
            add_context = add_context or {}
            add_context['ref'] = self.ref_id
        return super()._render_field(
            field, res_ids,
            engine=engine,
            compute_lang=compute_lang,
            set_lang=set_lang,
            add_context=add_context,
            options=options,
        )