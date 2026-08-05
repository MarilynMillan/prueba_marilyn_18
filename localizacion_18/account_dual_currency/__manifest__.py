# -*- coding: utf-8 -*-
{
    'name': "Venezuela: Account Dual Currency",
    'category': 'Account',
    'license': 'Other proprietary',
    'summary': """Esta aplicación permite manejar dualidad de moneda en Contabilidad.""",
    'author': 'José Luis Vizcaya López',
    'company': 'José Luis Vizcaya López',
    'maintainer': 'José Luis Vizcaya López',
    'website': 'https://github.com/birkot',
    'description': """
    
        - Mantener como moneda principal Bs y $ como secundaria.
        - Facturas en Bs pero manteniendo deuda en $.
        - Tasa individual para cada Factura de Cliente y Proveedor.
        - Tasa individual para Asientos contables.
        - Visualización de Débito y Crédito en ambas monedas en los apuntes contables.
        - Conciliación total o parcial de $ y Bs en facturas.
        - Registro de pagos en facturas con tasa diferente a la factura.
        - Registro de anticipos en el módulo de Pagos de Odoo, manteniendo saldo a favor en $ y Bs.
        - Informe de seguimiento en $ y Bs a la tasa actual.
        - Reportes contables en $ (Vencidas por Pagar, Vencidas por Cobrar y Libro mayor de empresas)
        - Valoración de inventario en $ y Bs a la tasa actual

    """,
    'depends': [
                'base','base_contable','account','account_reports',
                'account_accountant','analytic','account_debit_note','product'
                ],
    'data':[
        #'security/ir.model.access.csv',
        
    ],
    'assets': {
        'web.assets_backend': [
            #'account_dual_currency/static/src/components/filter_date.xml',
            'account_dual_currency/static/src/components/bank_reconciliation/kanban.js',
            'account_dual_currency/static/src/components/bank_reconciliation/bank_rec_form.xml',
            'account_dual_currency/static/src/components/filter.xml',
            'account_dual_currency/static/src/components/account_payment.xml',
            ##'account_dual_currency/static/src/components/filters.js',
            'account_dual_currency/static/src/js/**/*',
            'account_dual_currency/static/src/xml/**/*',
        ],
        'web.assets_qweb': [
            'account_dual_currency/static/src/components/filter.xml',
        ],
    },
    'images': [
        'static/description/thumbnail.png',
    ],
    'live_test_url': 'https://demo17-venezuela.odoo.com/web/login',
    "price": 3000,
    "currency": "USD",
    'installable' : True,
    'application' : False,
}

