import logging
from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError

_logger = logging.getLogger(__name__)

MAX_SESSIONS = 3


class Event(models.Model):
    _inherit = 'event.event'

    event_table_ids = fields.Many2many(
        'event.booking.table',
        string='Tables',
        compute='_compute_event_table_ids',
        readonly=False,
        store=True,
    )
    network_id = fields.Many2one(
        'membership.network',
        string='Network',
        compute='_compute_network_id',
        readonly=False,
        store=True,
    )
    members_only = fields.Boolean(string="Members Only")
    session_count = fields.Integer(
        string='Number of Sessions',
        default=2,
        required=True,
        help=f'Number of table rotation sessions in this event (1-{MAX_SESSIONS})'
    )

    @api.depends('event_type_id')
    def _compute_network_id(self):
        for event in self:
            if event.event_type_id.network_id:
                event.network_id = event.event_type_id.network_id

    @api.depends('event_type_id')
    def _compute_event_table_ids(self):
        for event in self:
            if event.event_type_id.event_table_ids:
                event.event_table_ids = event.event_type_id.event_table_ids

    @api.constrains('session_count')
    def _check_session_count(self):
        for event in self:
            if event.session_count < 1 or event.session_count > MAX_SESSIONS:
                raise ValidationError(_(f'Number of sessions must be between 1 and {MAX_SESSIONS}'))

    def action_assign_tables(self):
        self.ensure_one()

        if not self.event_table_ids:
            raise UserError(_("Please configure tables for this event first."))

        if not self.registration_ids:
            raise UserError(_("No registrations found for this event."))

        registrations_with_partners = self.registration_ids.filtered(lambda r: r.partner_id)
        attendee_count = len(registrations_with_partners)

        if attendee_count == 0:
            raise UserError(_("No registrations with partners found. Please ensure registrations have partners assigned."))

        total_capacity = sum(table.capacity for table in self.event_table_ids)
        if total_capacity < attendee_count:
            raise UserError(_(
                "Insufficient table capacity. Need %s seats but only have %s. "
                "Please add more tables or increase capacity."
            ) % (attendee_count, total_capacity))

        clear_values = {f'session_{i}_table_id': False for i in range(1, MAX_SESSIONS + 1)}
        registrations_with_partners.write(clear_values)

        forbidden_pairs = self._build_forbidden_pairs()
        table_assignments = {
            i: {table.id: [] for table in self.event_table_ids}
            for i in range(1, MAX_SESSIONS + 1)
        }
        current_companions = {}

        for session in range(1, self.session_count + 1):
            for registration in registrations_with_partners:
                partner = registration.partner_id

                already_assigned_tables = set()
                for prev_session in range(1, session):
                    prev_table = getattr(registration, f'session_{prev_session}_table_id', None)
                    if prev_table:
                        already_assigned_tables.add(prev_table.id)

                best_table = self._find_best_table(
                    partner=partner,
                    session=session,
                    forbidden_pairs=forbidden_pairs,
                    current_companions=current_companions,
                    table_assignments=table_assignments,
                    already_assigned_tables=already_assigned_tables,
                )

                if best_table:
                    self._assign_table_to_registration(registration, best_table, session)
                    table_assignments[session][best_table.id].append(partner.id)

                    if partner.id not in current_companions:
                        current_companions[partner.id] = set()
                    for occupant_id in table_assignments[session][best_table.id]:
                        if occupant_id != partner.id:
                            current_companions[partner.id].add(occupant_id)
                            if occupant_id not in current_companions:
                                current_companions[occupant_id] = set()
                            current_companions[occupant_id].add(partner.id)

        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('Success'),
                'message': _('%s attendees assigned to %s session(s)') % (attendee_count, self.session_count),
                'type': 'success',
                'sticky': False,
            }
        }

    def assign_tables_to_registration(self, registration):
        """
        Assign tables to a single registration (used during frontend registration).
        Uses event.registration for forbidden pairs instead of table history.
        """
        self.ensure_one()

        if not self.event_table_ids or not registration.partner_id:
            return

        partner = registration.partner_id

        # Build forbidden pairs from past event registrations
        forbidden_pairs = {}
        forbidden_ids = set()
        past_regs = self.env['event.registration'].search([
            ('partner_id', '=', partner.id),
            ('state', '=', 'done'),
            ('event_id', '!=', self.id),
        ])
        for reg in past_regs:
            for session in range(1, MAX_SESSIONS + 1):
                table = getattr(reg, f'session_{session}_table_id', None)
                if not table:
                    continue
                same_table_regs = self.env['event.registration'].search([
                    ('event_id', '=', reg.event_id.id),
                    ('state', '=', 'done'),
                    ('partner_id', '!=', partner.id),
                    (f'session_{session}_table_id', '=', table.id),
                ])
                forbidden_ids.update(same_table_regs.mapped('partner_id').ids)
        forbidden_pairs[partner.id] = forbidden_ids

        current_companions = {}

        # Build current table assignments from existing registrations
        table_assignments = {i: {table.id: [] for table in self.event_table_ids} for i in range(1, MAX_SESSIONS + 1)}
        for existing_reg in self.registration_ids:
            if existing_reg.id == registration.id or not existing_reg.partner_id:
                continue
            for session in range(1, MAX_SESSIONS + 1):
                assigned_table = getattr(existing_reg, f'session_{session}_table_id', None)
                if assigned_table:
                    table_assignments[session][assigned_table.id].append(existing_reg.partner_id.id)

        already_assigned_tables = set()
        for session in range(1, self.session_count + 1):
            best_table = self._find_best_table(
                partner=partner,
                session=session,
                forbidden_pairs=forbidden_pairs,
                current_companions=current_companions,
                table_assignments=table_assignments,
                already_assigned_tables=already_assigned_tables,
            )
            if best_table:
                self._assign_table_to_registration(registration, best_table, session)
                already_assigned_tables.add(best_table.id)
                table_assignments[session][best_table.id].append(partner.id)

                if partner.id not in current_companions:
                    current_companions[partner.id] = set()
                for occupant_id in table_assignments[session][best_table.id]:
                    if occupant_id != partner.id:
                        current_companions[partner.id].add(occupant_id)

    def _build_forbidden_pairs(self):
        """
        Build forbidden pairs from event.registration directly.
        Two partners are forbidden if they sat at the same table in any past event.
        """
        forbidden_pairs = {}
        partners = self.registration_ids.mapped('partner_id')

        for partner in partners:
            forbidden_ids = set()
            past_regs = self.env['event.registration'].search([
                ('partner_id', '=', partner.id),
                ('state', '=', 'done'),
                ('event_id', '!=', self.id),
            ])
            for reg in past_regs:
                for session in range(1, MAX_SESSIONS + 1):
                    table = getattr(reg, f'session_{session}_table_id', None)
                    if not table:
                        continue
                    same_table_regs = self.env['event.registration'].search([
                        ('event_id', '=', reg.event_id.id),
                        ('state', '=', 'done'),
                        ('partner_id', '!=', partner.id),
                        (f'session_{session}_table_id', '=', table.id),
                    ])
                    forbidden_ids.update(same_table_regs.mapped('partner_id').ids)
            forbidden_pairs[partner.id] = forbidden_ids

        return forbidden_pairs

    def _find_best_table(self, partner, session, forbidden_pairs, current_companions, table_assignments, already_assigned_tables=None):
        if already_assigned_tables is None:
            already_assigned_tables = set()

        best_table = None
        min_conflicts = float('inf')
        max_occupancy = -1

        for table in self.event_table_ids.sorted('name'):
            if table.id in already_assigned_tables:
                continue

            occupants = table_assignments[session].get(table.id, [])
            if len(occupants) >= table.capacity:
                continue

            conflicts = 0
            for occupant_id in occupants:
                if occupant_id in forbidden_pairs.get(partner.id, set()):
                    conflicts += 10
                if occupant_id in current_companions.get(partner.id, set()):
                    conflicts += 5

            occupancy = len(occupants)
            if conflicts < min_conflicts or (conflicts == min_conflicts and occupancy > max_occupancy):
                min_conflicts = conflicts
                max_occupancy = occupancy
                best_table = table

        if not best_table:
            available_tables = [
                (table, len(table_assignments[session].get(table.id, [])))
                for table in self.event_table_ids
                if len(table_assignments[session].get(table.id, [])) < table.capacity
                and table.id not in already_assigned_tables
            ]
            if available_tables:
                best_table = min(available_tables, key=lambda x: x[1])[0]

        return best_table

    def _assign_table_to_registration(self, registration, table, session):
        field_name = f'session_{session}_table_id'
        setattr(registration, field_name, table.id)

    def _network_members(self):
        if self.network_id and self.members_only:
            return self.network_id.member_ids.filtered(
                lambda member: member.membership_state == 'invoiced'
            ).ids
        return self.network_id.member_ids.ids

    def _create_network_registrations(self):
        partners = self.env['res.partner'].browse(self._network_members())
        for partner in partners:
            existing = self.env['event.registration'].search([
                ('event_id', '=', self.id),
                ('partner_id', '=', partner.id),
            ], limit=1)
            if existing:
                continue
            self.env['event.registration'].create({
                'event_id': self.id,
                'partner_id': partner.id,
                'name': partner.name,
                'email': partner.email,
                'phone': partner.phone,
                'state': 'open',
            })

    # def action_invite_contacts(self):
    #     # self._create_network_registrations()
    #     network_name = self.network_id.name or ''
    #     body_arch = self.env['ir.ui.view']._render_template(
    #         'membership_network.membership_network_default_template',
    #         values={
    #             'network_name': network_name,
    #             'event_name': self.name,
    #             'event_url': self.event_register_url,
    #             'company_id': self.env.company,
    #         }
    #     )
    #     return {
    #         'name': 'Mass Mail Invitation',
    #         'type': 'ir.actions.act_window',
    #         'res_model': 'mailing.mailing',
    #         'view_mode': 'form',
    #         'target': 'current',
    #         'context': {
    #             'default_mailing_model_id': self.env.ref('base.model_res_partner').id,
    #             'default_subject': _("You're invited to join %s!", network_name),
    #             'default_mailing_domain': repr([('id', 'in', self._network_members())]),
    #             'default_body_arch': body_arch,
    #         },
    #     }

    def action_invite_contacts(self):
        network_name = self.network_id.name or ''

        if self.network_id and self.members_only:
            mailing_domain = [
                ('network_ids', 'in', self.network_id.id),
                ('membership_state', 'in', ['paid', 'invoiced']),
            ]
        elif self.network_id:
            mailing_domain = [('network_ids', 'in', self.network_id.id)]
        else:
            mailing_domain = []

        body_arch = self.env['ir.ui.view']._render_template(
            'membership_network.membership_network_default_template',
            values={
                'network_name': network_name,
                'event_name': self.name,
                'event_url': self.event_register_url,
                'company_id': self.env.company,
                'company_logo': 'data:image/png;base64,' + (
                    self.env.company.logo.decode('utf-8')
                    if isinstance(self.env.company.logo, bytes) else self.env.company.logo or ''
                ),
            }
        )
        return {
            'name': 'Mass Mail Invitation',
            'type': 'ir.actions.act_window',
            'res_model': 'mailing.mailing',
            'view_mode': 'form',
            'target': 'current',
            'context': {
                'default_mailing_model_id': self.env.ref('base.model_res_partner').id,
                'default_subject': _("You're invited to %s!", self.name),
                'default_mailing_domain': repr(mailing_domain),
                'default_body_arch': body_arch,
                'default_ref_id': f'event.event,{self.id}',
            },
        }


