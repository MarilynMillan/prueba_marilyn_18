{
    'name': 'Report Global Sales Details',
    'version': '18.0.1.0.0',
    'category': 'Sales',
    'license': 'LGPL-3',
    'summary': 'Reporte detallado global de ventas y POS.',
    'author': 'Jules',
    'depends': ['base', 'sale', 'point_of_sale', 'account'],
    'data': [
        'security/ir.model.access.csv',
        'wizard/global_sales_details_wizard_view.xml',
        'report/global_sales_details_report.xml',
    ],
    'installable': True,
    'application': False,
    'auto_install': False,
}
