from odoo import models, fields

class SaleReport(models.Model):
    _inherit = "sale.report"

    price_total_usd = fields.Float(string="Total USD", readonly=True)

   