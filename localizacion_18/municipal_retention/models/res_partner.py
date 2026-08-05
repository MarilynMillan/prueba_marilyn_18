# -*- coding: utf -*-
import logging
from datetime import datetime, date
from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError

_logger = logging.getLogger("__name__")




class ResPartner(models.Model):
    _inherit = 'res.partner'


    muni_wh_agent = fields.Boolean(string='Retention agent', help='True if your partner is a municipal retention agent')
    diario_jrl_id = fields.Many2one('account.journal', string='diario',company_dependent=True)
    account_ret_muni_receivable_id = fields.Many2one('account.account', string='Cuenta Retencion Clientes', company_dependent=True)
    account_ret_muni_payable_id = fields.Many2one('account.account', string='Cuenta Retencion Proveedores', company_dependent=True)
    nit = fields.Char(string='NIT', help='Old tax identification number replaced by the current RIF')
    econ_act_license = fields.Char(string='License number', help='Economic activity license number')
    nifg = fields.Char(string='NIFG', help='Number assigned by Satrin')