# -*- coding: utf-8 -*-
{
    'name': 'CRM Event',
    'version': '1.0',
    'website': 'https://www.odoo.com/page/events',
    'category': 'Marketing/Events',
    'summary': 'Connection between CRM Lead and Event',
    'description': """
Organization and management of Events.
======================================
TODO
The event module allows you to efficiently organize events and all related tasks: planning, registration tracking,
attendances, etc.

Key Features
------------
* Manage your Events and Registrations
* Use emails to automatically confirm and send acknowledgments for any event registration
""",
    'depends': ['crm', 'event'], #, 'website_membership_form',
    'data': [
        'views/crm_lead_views.xml',
    ],

    'installable': True,
    'auto_install': False,
}
