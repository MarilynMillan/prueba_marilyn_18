# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
#################################################################################
# Author      : Grow Consultancy Services (<https://www.growconsultancyservices.com/>)
# Copyright(c): 2021-Present Grow Consultancy Services
# All Rights Reserved.
#
#
# This program is copyright property of the author mentioned above.
# You can`t redistribute it and/or modify it.
#
#
# You should have received a copy of the License along with this program.
#################################################################################
{
    # Application Information
    'name': 'Impresion fiscal por contabilidad',
    'version': '18.0.1.0.0',
    'category': 'Technical',
    'license': 'LGPL-3',

    'summary': """
Impresiom fiscal por contabilidad""",

    # Author Information
    'author': 'Grow Consultancy Services',
    'maintainer': 'Grow Consultancy Services',
    'website': 'http://www.growconsultancyservices.com',

    # Application Price Information
    'price': 0,
    'currency': 'USD',

    # Dependencies
    'depends': ['base', 'base_contable'],

    # Views
    'data': [
        #"security/ir.model.access.csv",
        #"views/product_brand_views.xml",
        "views/account_move_views.xml",
        #"wizard/wizard_report.xml",
        # 'view/'
        # wizard/
    ],

    # Application Main Image    
    'images': ['static/description/print.png'],

    # Technical
    'installable': True,
    'application': True,
    'auto_install': False,
    'active': False,
}
