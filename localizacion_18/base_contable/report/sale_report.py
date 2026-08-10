from odoo import models, fields

class SaleReport(models.Model):
    _inherit = "sale.report"

    tasa = fields.Float(string="Tasa del día", group_operator="avg", readonly=True)
    currency_usd_id = fields.Many2one('res.currency', string="USD Currency", readonly=True)
    price_total_usd = fields.Float(string="Total USD", readonly=True)
    price_unit_usd = fields.Float(string="Precio Unitario USD", readonly=True, group_operator="avg")

    def _select_additional_fields(self):
        res = super()._select_additional_fields()
        res['tasa'] = "s.x_tasa"
        res['currency_usd_id'] = "(SELECT id FROM res_currency WHERE name = 'USD' LIMIT 1)"
        res['price_total_usd'] = "TRUNC(SUM(l.price_total / NULLIF(s.x_tasa, 0))::numeric, 2)"
        res['price_unit_usd'] = "TRUNC(SUM(l.price_unit / NULLIF(s.x_tasa, 0))::numeric, 2)"
        return res

    def _group_by_sale(self):
        group_by = super()._group_by_sale()
        group_by += ", s.x_tasa"
        return group_by

    def _available_additional_pos_fields(self):
        res = super()._available_additional_pos_fields()
        res['tasa'] = "pos.tasa_dia"
        res['currency_usd_id'] = "(SELECT id FROM res_currency WHERE name = 'USD' LIMIT 1)"
        res['price_total_usd'] = "TRUNC(SUM(l.price_subtotal_incl / NULLIF(pos.tasa_dia, 0))::numeric, 2)"
        res['price_unit_usd'] = "TRUNC(SUM(l.price_unit / NULLIF(pos.tasa_dia, 0))::numeric, 2)"
        return res

    def _group_by_pos(self):
        group_by = super()._group_by_pos()
        group_by += ", pos.tasa_dia"
        return group_by
