from odoo import fields, models, api
from odoo.exceptions import UserError


class PosConfig(models.Model):
    _inherit = "pos.config"

    dual_currency = fields.Boolean(default=False,)
    company_rate = fields.Float(related='currency_id.rate',)
    second_currency = fields.Many2one('res.currency',)
    second_currency_rate = fields.Float(related='second_currency.rate')
    second_currency_symbol = fields.Char(related='second_currency.symbol')


class ResConfigSettings(models.TransientModel):
    _inherit = "res.config.settings"

    pos_dual_currency = fields.Boolean(related='pos_config_id.dual_currency',
                                       readonly=False)

    pos_second_currency = fields.Many2one(related='pos_config_id.second_currency',
                                          readonly=False,)

