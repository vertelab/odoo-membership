# -*- coding: utf-8 -*-

{
    'name': 'Membership form',
    'category': 'Website',
    'sequence': 166,
    'summary': 'A website for users to register them self as members.',
    'website': 'https://www.vertel.se',
    'description': "",
    'depends': ['website', 'membership', 'crm_event'],
    'data': [
        'views/membership_templates.xml',
        'security/ir.model.access.csv'
    ],
    'application': True,
}
