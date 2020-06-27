# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.


{
    'name': 'Membership Invoice FortNox',
    'version': '1.0',
    'category': 'memberhsip',
    'description': """
This module extends the invoicing capabilities for membership-module
    """,
    'depends': ['membership_invoice'],
    'data': [
        
        'views/partner_views.xml',
        # ~ 'views/product_views.xml',
        
    ],
    'website': 'vertel.se',
}
