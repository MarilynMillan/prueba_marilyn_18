# -*- coding: utf-8 -*-
from odoo import api, fields, models, _, Command

class ResCompany(models.Model):
    _inherit = "res.company"

    currency_id_dif = fields.Many2one("res.currency", compute='_compute_moneda_sec',precompute=True)

    def _compute_moneda_sec(self):
        self.currency_id_dif=self.currency_sec_id.id