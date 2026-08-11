# -*- coding: utf-8 -*-
{
    'name': "Módulo base localizacion contable  18",

    'summary': """Módulo base localizacion contable  18""",

    'description': """
       Módulo base localizacion contable  18
       Colaborador: Ing. Darrell Sojo
    """,
    'version': '18.0',
    'author': 'Darrell Sojo/ Frank service',
    'category': 'Módulo base localizacion contable  18',

    # any module necessary for this one to work correctly
    'depends': [
        'base',
        'stock',
        'account',
        'account_accountant',
        'account_debit_note',
        'sale',
        'purchase',
        'stock_account',
        'point_of_sale',
        'pos_receipt_extend',
        'pos_sale',
        ],

    # always loaded
    'data': [
        'vista/account_tax_views.xml',
        'vista/account_journal_views.xml',
        'vista/account_move_views.xml',###
        'vista/res_partner_views.xml',
        'vista/res_company_inherit.xml',
        'vista/modo_pago_view.xml',
        'vista/product_inherit_views.xml',
        'wizard/pago.xml',
        'vista/account_paiment_register_view.xml',
        'vista/purchase_inherit.xml',
        'vista/sale_inherit.xml',
        'vista/sale_report_view_tree.xml',
        'vista/stock_valuation_layer_base.xml',
        'wizar_report_igtf/wizard.xml',
        'wizar_report_igtf/reporte_view.xml',
        'security/ir.model.access.csv',
        ##'data/data.xml',
    ],
    'application': True,
    'license': 'OEEL-1',
}
