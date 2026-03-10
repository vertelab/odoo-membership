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
    'version': '1.0',
    'summary': 'Membership Network - allows partners to be members of multiple networks/clubs',
    'category': 'Human Resources', # Technical Settings|Localization|Payroll Localization|Account Charts|User types|Invoicing|Sales|Human Resources|Operations|Marketing|Manufacturing|Website|Theme|Administration|Appraisals|Sign|Helpdesk|Administration|Extra Rights|Other Extra Rights|
    'description': """
        Membership Network Module
        =========================
        
        This module extends Odoo's core membership functionality by allowing partners 
        to be members of multiple networks/clubs simultaneously.
        
        Features:
        ---------
        * Create multiple membership networks/clubs
        * Link networks to membership products
        * Track partner memberships in multiple networks
        * Each network membership has its own state, dates, and invoices
        * Smart buttons and dedicated tabs on partner form
    """,
    'author': 'Vertel AB',
    'website': 'https://vertel.se/apps/odoo-membership',
    'images': ['static/description/banner.png'],
    'license': 'AGPL-3',
    'depends': ["contacts", "event", "membership", "account", "report_glabels", "mass_mailing_event", "website_event"],
    'data': [
        'security/ir.model.access.csv',
        'data/network_data.xml',
        'data/ir_actions_server.xml',
        'views/membership_network_views.xml',
        'views/table_booking_views.xml',
        'views/table_booking_history_views.xml',
        'views/event_event_views.xml',
        'views/website_templates.xml',
        'views/res_partner_views.xml',
        'views/event_table_report.xml',
        'views/themes_templates.xml',
        'wizard/event_booking_table_wizard.xml'
    ],
    'demo': [],
    'application': False,
    'installable': True,    
    'auto_install': False,
}
