# -*- coding: utf-8 -*-

{
    'name': 'Portal event',
    'category': 'Website',
    'sequence': 166,
    'summary': 'Adds some stuff to the portal',
    'website': 'https://www.vertel.se',
    'description': "",
    'depends': ['portal', 'event',],
    'data': [
        'views/portal_templates.xml',
        'views/event_view.xml',
        'security/ir.model.access.csv'
    ],
    'application': True,
}
