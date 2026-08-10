# -*- coding: utf-8 -*-

from odoo import api, fields


class PosConfig(models.Model):
    _inherit = 'pos.order'


    tasa_dia = fields.Float(compute="_compute_tasa", store="True")