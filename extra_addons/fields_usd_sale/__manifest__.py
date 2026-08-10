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
    'name': 'Fields_usd_sale',
    'version': '18.0',
    'category': 'Sale',
    'license': 'LGPL-3',
    'summary': """Reporte de  ventas y punto de venta""",
    # Author Information
    'author': 'Ing Darrell Sojo/Colaborador:Ing Marilyn Millan',
    'website': '',

    # Application Price Information

    # Dependencies
    'depends': ['base', 'sale','point_of_sale', 'pos_receipt_extend'],

    # Views
    'data': [
       
        "views/sale_report_view.xml",
    ],

    # Application Main Image    
    #'images': ['static/description/print.png'],

    # Technical
    'installable': True,
    'application': True,
    'auto_install': False,
    'active': False,
}
