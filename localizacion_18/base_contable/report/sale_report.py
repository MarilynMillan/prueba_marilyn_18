from odoo import models, fields

class SaleReport(models.Model):
    _inherit = "sale.report"

    x_tasa = fields.Float(string="Tasa del día", group_operator="avg", readonly=True)
    price_total_usd = fields.Float(string="Total USD", readonly=True)

    def _select_sale(self):
        select_ = super()._select_sale()
        select_ += """,
            s.x_tasa as x_tasa,
            SUM(l.price_total / NULLIF(s.x_tasa, 0)) as price_total_usd"""
        return select_

    def _group_by_sale(self):
        group_by = super()._group_by_sale()
        group_by += """,
            s.x_tasa"""
        return group_by
