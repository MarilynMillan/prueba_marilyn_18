# -*- coding: utf-8 -*-
{
    'name': "Formatos de Factura/NC/ND forma Libre Localizacion V18",

    'summary': """Formatos de Factura/NC/ND forma Libre Localizacion V18""",

    'description': """
       Formatos de Factura/NC/ND forma Libre Localizacion V18.
    """,
    'version': '18.0',
    'author': 'Grupo Angendar/Alianza Frank Service',
    'category': 'Tools',
    'website': 'http://grupoangendar.com/',

    # any module necessary for this one to work correctly
    'depends': ['base','account','base_contable'],

    # always loaded
    'data': [
        'formatos/account_move_view.xml',
        'formatos/factura_libre.xml',
        #'vista/account_move_views.xml',
        
    ],
    'application': True,
    'active':False,
    'auto_install': False,
}
