# -*- coding: utf-8 -*-


from odoo import api, fields, models, _
from odoo.exceptions import RedirectWarning, UserError, ValidationError, AccessError
from odoo.tools import float_compare, date_utils
from odoo.tools.misc import formatLang, format_date
from contextlib import ExitStack, contextmanager

from datetime import date, timedelta
from collections import defaultdict
from itertools import zip_longest
from hashlib import sha256
from json import dumps

from odoo.tools import (
    date_utils,
    float_compare,
    float_is_zero,
    float_repr,
    format_amount,
    format_date,
    formatLang,
    frozendict,
    get_lang,
    index_exists,
    is_html_empty,
)

import ast
import json
import re
import warnings



class PurchaseOrder(models.Model):
    _inherit = 'purchase.order'


    x_tasa = fields.Float(compute='_compute_tasa',store=True, readonly=False,digits=(12, 4))



    @api.depends('date_order')
    @api.onchange('date_order')
    def _compute_tasa(self):
        result=1
        for selff in self:
            if selff.date_order:
                lista=selff.env['res.currency.rate'].search([('currency_id','=',selff.company_id.currency_sec_id.id),('name','<=',selff.date_order)],order='name desc',limit=1)
            if lista:
                result=lista.inverse_company_rate
            selff.x_tasa=result



class SaleOrder(models.Model):
    _inherit = 'sale.order'


    x_tasa = fields.Float(compute='_compute_tasa',store=True, readonly=False,digits=(12, 4))



    @api.depends('date_order')
    @api.onchange('date_order')
    def _compute_tasa(self):
        result=1
        for selff in self:
            if selff.date_order:
                lista=selff.env['res.currency.rate'].search([('currency_id','=',selff.company_id.currency_sec_id.id),('name','<=',selff.date_order)],order='name desc',limit=1)
            if lista:
                result=lista.inverse_company_rate
            selff.x_tasa=result

   