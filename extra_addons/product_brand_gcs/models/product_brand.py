# Part of Odoo. See LICENSE file for full copyright and licensing details.
from odoo import models, fields


class ProductBrandGCS(models.Model):
    _name = "product.brand.gcs"
    _description = "Product Brand GCS"

    name = fields.Char("Brand Name", index=True, required=True, copy=False, help="Product brand")
