# -*- coding: utf-8 -*-

{
    'name': 'CRM Campaign View',
    'category': 'CRM',
    'sequence': 166,
    'summary': 'Adds tree- and calender-view to campaigns and adds attributes to a campaign. Adds campaign code class.',
    'website': 'https://www.vertel.se',
    'description': "",
    'depends': ['mass_mailing',],
    'data': [
    	'views/utm_campaign_views.xml',
    	'security/ir.model.access.csv',
    ],
    'application': True,
}
