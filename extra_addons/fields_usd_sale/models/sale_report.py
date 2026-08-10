from odoo import models, fields

class SaleReport(models.Model):
    _inherit = "sale.report"

    tasa = fields.Float(string="Tasa del día", group_operator="avg", readonly=True)
    price_total_usd = fields.Float(string="Total USD", readonly=True)
    price_unit_usd = fields.Float(string="Precio Unitario USD", readonly=True, group_operator="avg")
    currency_usd_id = fields.Many2one('res.currency', string="USD Currency", readonly=True)

    def _select_sale(self):
        select_ = super()._select_sale()
        select_ += """,
            s.x_tasa as tasa,
            (SELECT id FROM res_currency WHERE name = 'USD' LIMIT 1) as currency_usd_id,
            TRUNC(CAST(SUM(l.price_total / NULLIF(s.x_tasa, 0)) AS numeric), 2) as price_total_usd,
            TRUNC(CAST(SUM(l.price_unit / NULLIF(s.x_tasa, 0)) AS numeric), 2) as price_unit_usd"""
        return select_


    def _group_by_sale(self):
        group_by = super()._group_by_sale()
        group_by += """,
            s.x_tasa"""
        return group_by

    def _select_pos(self):
        select_ = super()._select_pos()
        select_ += """,
            pos.tasa_dia as tasa,
            (SELECT id FROM res_currency WHERE name = 'USD' LIMIT 1) as currency_usd_id,
            TRUNC(CAST(SUM(l.price_subtotal_incl / NULLIF(pos.tasa_dia, 0)) AS numeric), 2) as price_total_usd,
            TRUNC(CAST(SUM(l.price_unit / NULLIF(pos.tasa_dia, 0)) AS numeric), 2) as price_unit_usd"""
        return select_

    def _group_by_pos(self):
        group_by = super()._group_by_pos()
        group_by += """,
            pos.tasa_dia"""
        return group_by
