# -*- coding: utf-8 -*-

{
    'name': 'Invoicing Plus',
    'summary': '''
        Small Improvements and Fixes to Invoicing Module''',

    'author': 'Space Integrated Solutions',
    'website': 'http://odootech.mn',
    'license': 'OPL-1',

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/master/odoo/addons/base/module/module_data.xml
    # for the full list
    'category': 'Accounting',
    'version': '14.0.1.0.0',
    'application': False,
    'installable': True,
    'auto_install': True,

    # any module necessary for this one to work correctly
    'depends': [
        'account',
    ],

    # always loaded
    'data': [
        'views/res_currency.xml',
        'templates/account_plus.xml',
    ],
}
