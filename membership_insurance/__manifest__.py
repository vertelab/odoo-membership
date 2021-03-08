{
    'name':'Membership Insurance',
    'description': 'Fields for administer members in insurance industry',
    'version':'1.0',
    'author':'Vertel AB',

    'data': [
        'views/insurance_invoice_views.xml',
        'views/res_partner_views.xml',
        'views/product_views.xml',
        'data/insurance.license.csv',
        'data/insurance.permission.csv',
        # ~ 'data/insurance.klientmedelskonto.product.csv',
        # ~ 'data/insurance.SFMbolag.product.csv',
        'data/insurance_data.xml',
        'security/ir.model.access.csv',
    ],
    'category': 'membership',
    'depends': ['l10n_se','crm','membership', 'membership_invoice'],
    'sequence': 5,
    'application': False,
}

