# Part of Odoo. See LICENSE file for full copyright and licensing details.
from odoo import models, fields


class ProductTemplate(models.Model):
    _inherit = "product.template"

    product_brand_gcs = fields.Many2one("product.brand.gcs", string="Marca del Producto", help="Select product brand")

    product_pesaje = fields.Boolean(default=False)
    lf_code = fields.Integer(string='LFCode', required=False)
    #code = fields.Char(string='Code', required=False)
    pbarcode = fields.Integer(string='BarCode', required=False)
    #unit_price = fields.Float(string='UnitPrice', required=False)
    weight_unit = fields.Integer(string='WeightUnit', required=False)
    deptment = fields.Integer(string='Deptment', required=False)
    tare = fields.Integer(string='Tare', required=False)
    shelf_time = fields.Integer(string='ShelfTime', required=False)
    fix_unit = fields.Integer(string='FixUnit', required=False)
    fix_weight = fields.Integer(string='FixWeight', required=False)
    tolerance = fields.Integer(string='Tolerance', required=False)
    message1 = fields.Integer(string='Message1', required=False)
    message2 = fields.Integer(string='Message2', required=False)
    account = fields.Integer(string='Account', required=False)
    multilabel = fields.Integer(string='MultiLabel', required=False)