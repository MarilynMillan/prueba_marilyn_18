# Part of Odoo. See LICENSE file for full copyright and licensing details.
from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError
from datetime import datetime, timedelta
from json import dumps

import ast
import json
import re
import warnings



class AccountMove(models.Model):
    _inherit = "account.move"


    def print_fiscal(self):
        data={}
        serpList =[]
        desc=0
        if self.currency_id==self.company_id.currency_id:
            factor=1
        else:
            factor=self.tasa
        for line in self.invoice_line_ids:
            if line.tax_ids.aliquot=='exempt':
                impuesto=0
            else:
                if line.tax_ids.aliquot=='general':
                    impuesto=1
                else:
                    if line.tax_ids.aliquot=='reduced':
                        impuesto=2
                    else:
                        if line.tax_ids=='additional':
                            impuesto=3

            data={
                'product':line.product_id.name,
                'cantidad':line.quantity,
                'precio':line.price_unit*factor,
                'impuesto':impuesto,
                }
            serpList.append(data)
            desc=desc+(line.price_unit*line.discount/100)
        #raise ValidationError(_('%s')%data["lineas"])
        enviar_lineas=json.dumps(serpList)
        #raise ValidationError(_('%s')%enviar_lineas)
        if self.partner_id.phone:
            phone=self.partner_id.phone
        else:
            phone='0000000'
        if self.partner_id.vat:
            vat=self.partner_id.vat
        else:
            vat='0000000'
        if self.partner_id.street:
            street=self.partner_id.street
        else:
            street='*********'
        valor='?cid='+str(self.id)
        valor=valor+'&numero_recibo='+self.invoice_number_next
        valor=valor+'&cliente='+self.partner_id.name
        valor=valor+'&telefono='+phone
        valor=valor+'&direccion='+street
        valor=valor+'&rif_cedula='+vat
        valor=valor+'&lineas='+enviar_lineas
        valor=valor+'&vendedor='+self.create_uid.name
        #valor=valor+'&descuento='+str(desc)
        #valor=valor+'&total_eq='+str(self.amount_total_eq)
        #valor=valor+'&bol_delivery=True'
        return {
            'type': 'ir.actions.act_url',
            'target': '_blank',
            'url':"http://localhost:8080/impresora_fiscal/cargar.php"+valor,
            #'url': self.config_id._get_pos_base_url() + '?config_id=%d' % self.config_id.id,
        }


    def credito_fiscal(self):
        if not self.fact_afect:
            raise ValidationError(_('Se necesita la factura afectada de ésta.'))
        busca=self.env['account.move'].search([('invoice_number_next','=',self.fact_afect)],limit=1)
        #raise ValidationError(_('%s')%busca)
        if busca:
            ref=busca.invoice_number_next
            valor='?pos_reference='+ref
            return {
            'type': 'ir.actions.act_url',
            'target': '_blank',
            'url':"http://localhost:8080/impresora_fiscal/nota_credito.php"+valor,
            #'url': self.config_id._get_pos_base_url() + '?config_id=%d' % self.config_id.id,
        }