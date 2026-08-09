from odoo import models, fields

class PosOrder(models.Model):
    _inherit = "pos.order"

    price_total_usd = fields.Float(string="Total USD", readonly=True)

   