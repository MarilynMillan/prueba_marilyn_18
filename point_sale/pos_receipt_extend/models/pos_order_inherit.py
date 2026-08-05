# -*- coding: utf-8 -*-


import logging
from datetime import datetime
from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError




class PosConfig(models.Model):
    _inherit = 'pos.order'


    #nb_caja_comp=fields.Char(string="Registro de Máquina Fiscal",compute='_compute_nb_caja')
    nb_caja=fields.Char(string="Registro de nombre de la caja")
    nro_nc_seniat = fields.Char()
    nro_fact_seniat = fields.Char()
    status_impresora = fields.Char(default="no")
    tipo = fields.Char(default="venta")
    tasa_dia = fields.Float(compute="_compute_tasa")

    url_nota_credito=fields.Char(string="Imprimir Nota de Credito",readonly="True")
    id_order_afectado=fields.Char()
    link=fields.Char(compute='_compute_link')


    @api.depends('date_order')
    def _compute_tasa(self):
        for record in self:
            # 1. Obtener la fecha (solo la parte de la fecha) del campo Datetime de la orden.
            order_date = record.date_order.date() if record.date_order else fields.Date.today()
            
            # 2. Buscar la tasa más reciente (con 'name' <= fecha de la orden) para la moneda secundaria.
            # NOTA: Usamos la variable 'order_date' SIN comillas.
            lista_tasa = record.env['res.currency.rate'].search([
                ('currency_id', '=', record.env.company.currency_sec_id.id),
                ('name', '<=', order_date) 
            ], order='name desc', limit=1)

            # 3. Asignar el valor de la tasa
            if lista_tasa:
                record.tasa_dia = lista_tasa.inverse_company_rate
            else:
                record.tasa_dia = 1.0 # o el valor predeterminado que uses



    """def refund(self):
        super().refund()
        self.nro_fact_seniat=0"""

    #@api.depends('state')
    @api.onchange('state')
    def _compute_link(self):
        valor_url='http://localhost:8080/impresora_fiscal/nota_credito.php'
        for selff in self:
            #selff.link=valor_url+'?id_order_afectado='+str(selff.id_order_afectado)+'&order_nc='+str(selff.id)+'&pos_reference='+str(selff.pos_reference) 
            selff.link=valor_url+'?id_order_afectado='+str(selff.id_order_afectado)+'&order_nc='+str(selff.id)+'&pos_reference='+str(selff.pos_reference) 
            selff.url_nota_credito=selff.link

class PosOrderLine(models.Model):
    _inherit = 'pos.order.line'

    status_impresora=fields.Char(related='order_id.status_impresora')
    tipo = fields.Char(related='order_id.tipo')
    tasa_dia = fields.Float(compute="_compute_tasa")


    def _compute_tasa(self):
        for record in self:
            record.tasa_dia = record.order_id.tasa_dia


class PosMakePayment(models.TransientModel):
    _inherit = 'pos.make.payment'

    def check(self):
        res = super(PosMakePayment, self).check()
        ordenes = self.env['pos.order'].browse(self.env.context.get('active_id', False))
        pos_reference=ordenes.pos_reference
        actualiza=self.env['pos.order'].search([('pos_reference','=',pos_reference),('amount_total','>','0')])
        for det in actualiza:
            id_order_org=det.id
        ordenes.id_order_afectado=id_order_org
        ordenes.tipo="devolucion"

        #raise UserError(_('pos_reference= %s')%ordenes.pos_reference)
