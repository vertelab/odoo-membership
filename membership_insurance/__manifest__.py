{
    'name':'Membership Insurance',
    'description': 'Fields for administer members in insurance industry',
    'version':'1.0',
    'author':'Vertel AB',

    'data': [
        'views/res_partner_views.xml',
        'data/insurance.license.csv',
        'data/insurance.permission.csv',
        'security/ir.model.access.csv'
    ],
    'category': 'membership',
    'depends': ['crm','membership'],
    'sequence': 5,
    'application': False,
}

