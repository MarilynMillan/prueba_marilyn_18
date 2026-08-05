# -*- coding: utf-8 -*-
from odoo import api, fields, models, _, Command
from odoo.exceptions import UserError, ValidationError, AccessError, RedirectWarning
from odoo.tools import (
    date_utils,
    float_compare,
    float_is_zero,
    format_amount,
    format_date,
    formatLang,
    frozendict,
    get_lang,
    is_html_empty,
    sql
)
import json



class AccountMove(models.Model):
    _inherit = 'account.move'

    currency_id_dif = fields.Many2one("res.currency",default=lambda self: self.env.company.currency_id_dif.id )
    amount_residual_usd = fields.Monetary(currency_field='currency_id_dif', digits='Dual_Currency', copy=False)

    """def action_post(self):
        res=super(AccountMove, self).action_post()
        #raise UserError(_("sss"))
        self.amount_residual_usd=self.amount_residual
        for line in self.line_ids:
            line.update_usd()"""
        

class AccountMoveLine(models.Model):
    _inherit = 'account.move.line'

    balance_usd = fields.Monetary(currency_field='currency_id_dif')
    #balance_usd = fields.Float(compute='_compute_balance_usd',precompute=True, store=True)
    currency_id_dif = fields.Many2one("res.currency", related="move_id.currency_id_dif", store=True)

    debit_usd = fields.Monetary(currency_field='currency_id_dif', string='Débito $' , store=True)
    credit_usd = fields.Monetary(currency_field='currency_id_dif', string='Crédito $', store=True)
    conv_credit_debit_balanc = fields.Char(default='no')

    #balance_usd = fields.Monetary(string='Balance Ref.',
                                  #currency_field='currency_id_dif', store=True, readonly=False,
                                  #compute='_compute_balance_usd',
                                  #default=lambda self: self._compute_balance_usd(),
                                  #help="Technical field holding the debit_usd - credit_usd in order to open meaningful graph views from reports")

    def update_usd(self):
        for selff in self:
            selff.balance_usd=selff.balance/selff.move_id.tasa
            valor=selff.credit/selff.move_id.tasa if selff.move_id.tasa!=0 else selff.credit
            selff.credit_usd=valor
            valor2=selff.debit/selff.move_id.tasa if selff.move_id.tasa!=0 else selff.debit
            selff.debit_usd=valor2
            selff.conv_credit_debit_balanc='si'