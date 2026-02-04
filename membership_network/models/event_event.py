import logging
import random
from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError

_logger = logging.getLogger(__name__)

# Maximum number of table rotation sessions supported
MAX_SESSIONS = 3


class Event(models.Model):
    _inherit = 'event.event'

    event_table_ids = fields.Many2many("event.booking.table", string="Tables")
    network_id = fields.Many2one('membership.network', string='Network',
        help='Link this event to a membership network to invite all members')
    session_count = fields.Integer(
        string='Number of Sessions',
        default=2,
        required=True,
        help=f'Number of table rotation sessions in this event (1-{MAX_SESSIONS})'
    )

    @api.constrains('session_count')
    def _check_session_count(self):
        for event in self:
            if event.session_count < 1 or event.session_count > MAX_SESSIONS:
                raise ValidationError(_(f'Number of sessions must be between 1 and {MAX_SESSIONS}'))


    def action_assign_tables(self):
        """
        Bulk assign tables to all registrations in the event.
        Reuses assign_tables_to_registration for each registration.
        """
        self.ensure_one()
        
        if not self.event_table_ids:
            raise UserError(_("Please configure tables for this event first."))
        
        if not self.registration_ids:
            raise UserError(_("No registrations found for this event."))
        
        # Count only registrations with partners
        registrations_with_partners = self.registration_ids.filtered(lambda r: r.partner_id)
        attendee_count = len(registrations_with_partners)
        
        if attendee_count == 0:
            raise UserError(_("No registrations with partners found. Please ensure registrations have partners assigned."))
        
        # Validate capacity
        total_capacity = sum(table.capacity for table in self.event_table_ids)
        
        if total_capacity < attendee_count:
            raise UserError(_(
                "Insufficient table capacity. Need %s seats but only have %s. "
                "Please add more tables or increase capacity."
            ) % (attendee_count, total_capacity))
        
        # Clear existing assignments dynamically
        clear_values = {f'reserved_table_{i}_id': False for i in range(1, MAX_SESSIONS + 1)}
        registrations_with_partners.write(clear_values)
        
        # Assign tables to each registration
        for registration in registrations_with_partners:
            self.assign_tables_to_registration(registration)
        
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
        Uses the same smart algorithm but only assigns for this one person.
        """
        self.ensure_one()
        
        if not self.event_table_ids or not registration.partner_id:
            return
        
        # Build forbidden pairs from historical data
        forbidden_pairs = {}
        partner = registration.partner_id
        history = self.env['event.booking.table.history'].search([
            ('partner_ids', 'in', partner.id)
        ])
        all_companions = history.mapped('partner_ids')
        forbidden_pairs[partner.id] = set(all_companions.ids) - {partner.id}
        
        # Track companions within current event (from other registrations)
        current_companions = {}
        
        # Build current table assignments from existing registrations
        table_assignments = {i: {} for i in range(1, MAX_SESSIONS + 1)}
        for table in self.event_table_ids:
            for session in range(1, MAX_SESSIONS + 1):
                table_assignments[session][table.id] = []
        
        # Populate with existing assignments
        for existing_reg in self.registration_ids:
            if existing_reg.id == registration.id or not existing_reg.partner_id:
                continue
            
            for session in range(1, MAX_SESSIONS + 1):
                field_name = f'reserved_table_{session}_id'
                reserved_table = getattr(existing_reg, field_name, None)
                if reserved_table:
                    table_assignments[session][reserved_table.id].append(existing_reg.partner_id.id)
        
        # Assign tables for each session
        already_assigned_tables = set()  # Track tables already assigned to this person
        
        for session in range(1, self.session_count + 1):
            # Find best table for this partner (excluding already assigned tables)
            best_table = self._find_best_table(
                partner=partner,
                session=session,
                forbidden_pairs=forbidden_pairs,
                current_companions=current_companions,
                table_assignments=table_assignments,
                already_assigned_tables=already_assigned_tables
            )
            
            if best_table:
                # Assign the table
                self._assign_table_to_registration(registration, best_table, session)
                
                # Track this table as assigned
                already_assigned_tables.add(best_table.id)
                
                # Update tracking for next session
                table_assignments[session][best_table.id].append(partner.id)
                
                if partner.id not in current_companions:
                    current_companions[partner.id] = set()
                
                for occupant_id in table_assignments[session][best_table.id]:
                    if occupant_id != partner.id:
                        current_companions[partner.id].add(occupant_id)

    def _build_forbidden_pairs(self):
        """
        Build a dictionary of forbidden partner pairs from historical table data.
        Returns: {partner_id: set(forbidden_partner_ids)}
        """
        forbidden_pairs = {}
        
        # Get all partners from registrations
        partners = self.registration_ids.mapped('partner_id')
        
        for partner in partners:
            # Find all historical table records this partner was part of
            history = self.env['event.booking.table.history'].search([
                ('partner_ids', 'in', partner.id)
            ])
            
            # Get all partners from those tables (excluding current partner)
            forbidden_ids = set(history.mapped('partner_ids').ids) - {partner.id}
            
            forbidden_pairs[partner.id] = forbidden_ids
        
        return forbidden_pairs

    def _find_best_table(self, partner, session, forbidden_pairs, current_companions, table_assignments, already_assigned_tables=None):
        """
        Find the best table for a partner in a given session.
        Minimizes conflicts with both historical and current event companions.
        Avoids assigning the same table twice to the same person.
        """
        if already_assigned_tables is None:
            already_assigned_tables = set()
        
        best_table = None
        min_conflicts = float('inf')
        
        for table in self.event_table_ids:
            # Skip tables already assigned to this person in other sessions
            if table.id in already_assigned_tables:
                continue
            
            # Get current occupants of this table in this session
            occupants = table_assignments[session].get(table.id, [])
            
            # Check capacity
            if len(occupants) >= table.capacity:
                continue
            
            # Calculate conflicts
            conflicts = 0
            for occupant_id in occupants:
                # Historical conflict (heavy penalty - 10 points)
                if occupant_id in forbidden_pairs.get(partner.id, set()):
                    conflicts += 10
                
                # Current event conflict (medium penalty - 5 points)
                if occupant_id in current_companions.get(partner.id, set()):
                    conflicts += 5
            
            # Track best table
            if conflicts < min_conflicts:
                min_conflicts = conflicts
                best_table = table
            elif conflicts == min_conflicts and best_table:
                # Tie-breaker: prefer less full table
                if len(occupants) < len(table_assignments[session][best_table.id]):
                    best_table = table
        
        # Fallback: if no table found (shouldn't happen), assign to least full table
        if not best_table:
            available_tables = [
                (table, len(table_assignments[session].get(table.id, [])))
                for table in self.event_table_ids
                if len(table_assignments[session].get(table.id, [])) < table.capacity
                and table.id not in already_assigned_tables  # Exclude already assigned
            ]
            if available_tables:
                best_table = min(available_tables, key=lambda x: x[1])[0]
        
        return best_table

    def _assign_table_to_registration(self, registration, table, session):
        """
        Assign a table to a registration for a specific session.
        Dynamically sets reserved_table_X_id based on session number.
        """
        field_name = f'reserved_table_{session}_id'
        setattr(registration, field_name, table.id)

    def action_finalize_registrations(self):
        self.ensure_one()

        # We only care about people who were assigned a table and actually attended
        attended_registrations = self.registration_ids.filtered(
            lambda r: r.reserved_table_id and r.state == 'done'
        )

        # Group partners by table
        seating_results = {}
        for reg in attended_registrations:
            table_id = reg.reserved_table_id.id
            if table_id not in seating_results:
                seating_results[table_id] = []
            seating_results[table_id].append(reg.partner_id.id)

        # Create the permanent history records
        for table_id, partner_ids in seating_results.items():
            self.env['event.booking.table.history'].create({
                'name': f"{self.name} - Table {table_id}",
                'event_id': self.id,
                'table_id': table_id,
                'partner_ids': [(6, 0, partner_ids)]
            })

        return True


class EventRegistration(models.Model):
    _inherit = 'event.registration'

    reserved_table_1_id = fields.Many2one(
        'event.booking.table',
        string="Reserved Table 1"
    )

    reserved_table_1_name = fields.Char(
        string="Reserved Table 1 Name",
        related="reserved_table_1_id.name"
    )

    reserved_table_2_id = fields.Many2one(
        'event.booking.table',
        string="Reserved Table 2"
    )

    reserved_table_2_name = fields.Char(
        string="Reserved Table 2 Name",
        related="reserved_table_2_id.name"
    )

    reserved_table_3_id = fields.Many2one(
        'event.booking.table',
        string="Reserved Table 3"
    )

    reserved_table_3_name = fields.Char(
        string="Reserved Table 3 Name",
        related="reserved_table_3_id.name"
    )

    network_id = fields.Many2one(
        'membership.network',
        string="Network",
        related="event_id.network_id",
    )
    
    network_name = fields.Char(
        string="Network Name",
        related="network_id.name",
    )



    @api.model_create_multi
    def create(self, vals_list):
        registrations = super().create(vals_list)
        
        for registration in registrations:
            # Ensure partner_id is set before table assignment
            if not registration.partner_id and registration.email:
                # Try to find existing partner by email
                partner = self.env['res.partner'].sudo().search([
                    ('email', '=', registration.email)
                ], limit=1)
                
                if partner:
                    # Set the partner on registration
                    registration.partner_id = partner
                elif registration.event_id.network_id:
                    # For network events, partner MUST exist (membership required)
                    raise UserError(_(
                        'No partner found with email "%s". '
                        'This event requires network membership. '
                        'Please ensure you are registered in the system.'
                    ) % registration.email)
                else:
                    # For non-network events, create partner
                    partner = self.env['res.partner'].sudo().create({
                        'name': registration.name,
                        'email': registration.email,
                        'phone': registration.phone,
                        'company_type': 'person',
                    })
                    registration.partner_id = partner
            
            # Auto-assign tables if event has tables configured
            if registration.event_id.event_table_ids and registration.partner_id:
                registration.event_id.assign_tables_to_registration(registration)
        
        return registrations