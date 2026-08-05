# -*- coding: utf-8 -*-

{
    'name': "libro_ventas_compra_v18",

    'summary': """
        Libro de Ventas y Compras Odoo V18
        """,

    'description': """
        Libro de ventas y Compras Odoo V18
    """,

    'author': "Ing. Darrell Sojo",
    'website': "dsojo.tanfe@gmail.com",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/master/odoo/addons/base/module/module_data.xml
    # for the full list
    'category': 'Contabilidad',
    'version': '0.1',

    # any module necessary for this one to work correctly
     "depends" : ['base','account','base_contable','resumen_alicuota_libros'],

    # always loaded
    'data': [
        'security/ir.model.access.csv',
        'wizards_compras/wizard_libro_compras.xml',
        'reports/libro_compras.xml',
        'wizards_ventas/wizard_libro_ventas.xml',
        'reports/libro_ventas.xml',
        
        ],  
    # only loaded in demonstration mode
    'demo': [
    ],
    'installable': True,
}
