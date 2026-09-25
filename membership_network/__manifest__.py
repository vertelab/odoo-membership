# -*- coding: utf-8 -*-
##############################################################################
#
#    Copyright (C) {year} {company} info@vertel.se
#    All Rights Reserved
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as published
#    by the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################
#
# https://www.odoo.com/documentation/14.0/reference/module.html
#
{
    'name': 'Membership: Network',
    'version': '18.0.1.0.0',
    'summary': 'Membership Network - allows partners to be members of multiple networks/clubs.',
    'category': 'Human Resources', # Technical Settings|Localization|Payroll Localization|Account Charts|User types|Invoicing|Sales|Human Resources|Operations|Marketing|Manufacturing|Website|Theme|Administration|Appraisals|Sign|Helpdesk|Administration|Extra Rights|Other Extra Rights|
    'description': '''
Network
=======

    This module extends Odoo's core membership functionality by allowing partners 
            to be members of multiple networks/clubs simultaneously.

    Features:
            ---------
            * Create multiple membership networks/clubs
            * Link networks to membership products
            * Track partner memberships in multiple networks
            * Each network membership has its own state, dates, and invoices
            * Smart buttons and dedicated tabs on partner form

    Features:

        - Web integration: Exposes HTTP endpoints for external systems.
        - Automation: Scheduled jobs: Membership: Renew Expired Memberships, Membership: Send Expiration Reminders.
        - Guided Wizards: Step-by-step dialogs for data entry.
        - UI Integration: Extends 12 view(s) in the Odoo interface.
        - Extends Odoo: Builds on account.move, account.move.line, event.booking.table, event.booking.table.history.
    ''',
    'author': 'Vertel AB',
    'website': 'https://vertel.se/apps/odoo-membership/membership_network',
    'images': ['static/description/banner.png'],
    'license': 'AGPL-3',
    'depends': [
        "contacts", "event", "membership", "account", 
        "report_glabels", "mass_mailing_event", "website_event", 
        "event_attendee_badges", "event_partner_foodallergy"
    ],
    'data': [
        'security/ir.model.access.csv',

        'data/network_data.xml',
        'data/ir_actions_server.xml',
        'data/ir_actions_report.xml',
        'data/ir_cron.xml',
        'data/mail_template.xml',

        'views/membership_network_views.xml',
        'views/table_booking_views.xml',
        # 'views/table_booking_history_views.xml',
        'views/event_event_views.xml',
        'views/website_templates.xml',
        'views/product_views.xml',
        'views/res_partner_views.xml',
        # 'views/event_table_report.xml',
        'views/themes_templates.xml',
        'views/ir_ui_view.xml',
        'views/mailing_view.xml',
        'views/snippets_themes.xml',
        'views/portal_templates.xml',

        'wizard/event_booking_table_wizard.xml',
        'wizard/membership_invoice_views.xml',

        'demo/demo.xml'
    ],
    'demo': [
        'demo/demo.xml'
    ],
    'application': False,
    'installable': True,    
    'auto_install': False,
}
