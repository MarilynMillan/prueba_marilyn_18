# -*- coding: utf-8 -*-
{
    'name': "Reporte del Libro diario v18",

    'summary': """Reporte del Libro diario v18""",

    'description': """
       Reporte del Libro diario v18.
    """,
    'version': '18.0',
    'author': 'Darrell Sojo/ Frank service',
    'category': 'Tools',
    'website': 'dsojo.tranfe@gmail.com',

    # any module necessary for this one to work correctly
    'depends': ['base','account','base_contable'],

    # always loaded
    'data': [
        'report/reporte_view.xml',
        'wizard/wizard.xml',
        'security/ir.model.access.csv',
    ],
    'application': True,
    'active':False,
    'auto_install': False,
}
