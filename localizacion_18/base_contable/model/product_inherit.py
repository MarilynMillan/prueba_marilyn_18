# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError

class Productos(models.Model):
    _inherit = 'product.template'


    habilita_precio_div = fields.Boolean(default=False)
    list_price2 = fields.Float(string="Precio de Venta en USD", default=1,digits=(12, 4))
    standard_price_usd = fields.Float(digits=(12, 4))
    tasa_dia=fields.Float(digits=(12, 4),compute='_compute_tasa')

    def _compute_tasa(self):
        lista=self.env['res.currency.rate'].search([('currency_id','=',self.env.company.currency_sec_id.id)],limit=1,order='name desc')
        if lista:
            for det in lista:
                self.tasa_dia=det.inverse_company_rate

    #@api.onchange('standard_price_usd')
    #def actualiza_coste(self):
        #for selff in self:
            #if selff.standard_price_usd!=0:
                #selff.standard_price=selff.standard_price_usd*selff.tasa_dia

    @api.onchange('standard_price')
    def actualiza_coste(self):
        for selff in self:
            var_tasa=selff.tasa_dia
            if var_tasa==0:
                var_tasa=1
            if selff.standard_price!=0:
                selff.standard_price_usd=selff.standard_price/var_tasa

    @api.onchange('list_price2')
    def actualiza_precio_venta_bs(self):
        for selff in self:
            if selff.list_price2!=0 and selff.habilita_precio_div==True:
                selff.list_price=selff.list_price2*selff.tasa_dia

    def write(self,vals):
        super().write(vals)
        for selff in self:
            busca=selff.env['product.product'].search([('product_tmpl_id','=',selff.id)])
            if busca:
                for det in busca:
                    det.habilita_precio_divv=selff.habilita_precio_div
                    det.lst_price2=selff.list_price2

    #def actualiza_coste(self):



class ProductProduct(models.Model):
    _inherit = 'product.product'

    habilita_precio_divv = fields.Boolean(default=False)
    lst_price2 = fields.Float(string="Precio de Venta en USD", default=1,digits=(12, 4))
    standard_price_usd = fields.Float(digits=(12, 4))
    tasa_dia=fields.Float(digits=(12, 4),compute='_compute_tasa')

    def _compute_tasa(self):
        lista=self.env['res.currency.rate'].search([('currency_id','=',self.env.company.currency_sec_id.id)],limit=1,order='name desc')
        if lista:
            for det in lista:
                self.tasa_dia=det.inverse_company_rate

    """@api.onchange('standard_price_usd')
    def actualiza_coste(self):
        for selff in self:
            if selff.standard_price_usd!=0:
                selff.standard_price=selff.standard_price_usd*selff.tasa_dia
                selff.product_tmpl_id.standard_price_usd=selff.standard_price_usd"""

    @api.onchange('standard_price_usd')
    def actualiza_coste(self):
        for selff in self:
            var_tasa=selff.tasa_dia
            if var_tasa==0:
                var_tasa=1
            if selff.standard_price!=0:
                selff.standard_price_usd=selff.standard_price/var_tasa
                selff.product_tmpl_id.standard_price_usd=selff.standard_price_usd

    @api.onchange('lst_price2')
    def actualiza_precio_venta_bs(self):
        for selff in self:
            if selff.lst_price2!=0 and selff.habilita_precio_divv==True:
                selff.lst_price=selff.lst_price2*selff.tasa_dia