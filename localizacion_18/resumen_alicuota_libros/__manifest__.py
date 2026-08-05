# -*- coding: utf-8 -*-
{
    'name': "Modulo de resumen totales por alicuotas en las lineas de la factura",

    'summary': """Modulo de resumen totales por alicuotas en las lineas de la factura""",

    'description': """
       Modulo de resumen totales por alicuotas en las lineas de la factura
    """,
    'version': '18.0',
    'author': 'Ing. Darrell Sojo / Alianza Frank Service',
    'category': 'Tools',

    # any module necessary for this one to work correctly
    'depends': [
        'base',
        'account',
        'account_accountant',
        'base_contable',
        'account_debit_note',
        'iva_retention',
    ],

    # always loaded
    'data': [
        'security/ir.model.access.csv',
        'view/account_move_view.xml',
    ],
    'application': True,
}
