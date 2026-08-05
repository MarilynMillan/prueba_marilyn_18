# -*- coding: utf-8 -*-

from odoo import models, fields, api,_
from datetime import timedelta, date, datetime
from odoo.exceptions import UserError

from pytz import timezone
from bs4 import BeautifulSoup
import requests
import urllib3
urllib3.disable_warnings()
#Moneda..
class CurrencyRate(models.Model):
    _inherit = "res.currency.rate"

    #_sql_constraints = [('unique_name', 'CHECK(1=1)', 'Only one currency rate per day allowed!')]
    _sql_constraints = [('unique_name', 'CHECK(1=1)', 'Only one currency rate per day allowed!')]
    #currency_id = fields.Many2one('res.currency',readonly=False,copied=False)


    def central_bank(self):
        url = "https://www.bcv.org.ve/"
        req = requests.get(url, verify=False)
        active_euro=False

        status_code = req.status_code
        if status_code == 200:

            html = BeautifulSoup(req.text, "html.parser")
            # Dolar
            dolar_container = html.find('div', {'id': 'dolar'})
            # Usamos .text para obtener solo el número y .strip() para limpiar espacios
            dolar_valor = dolar_container.find('strong').text.strip()
            # Quitamos el punto de miles y cambiamos la coma decimal por punto
            dolar = float(dolar_valor.replace('.', '').replace(',', '.'))
            # Euro
            euro_container = html.find('div', {'id': 'euro'})
            euro_valor = euro_container.find('strong').text.strip()
            euro = float(euro_valor.replace('.', '').replace(',', '.'))

            if self.currency_id.name == 'USD':
                bcv = dolar
            elif self.currency_id.name == 'EUR':
                bcv = euro
            else:
                bcv = False
            id_usd=self.env['res.currency'].search([('name','=','USD')],limit=1)
            id_euro=self.env['res.currency'].search([('name','=','EUR')],limit=1)
            if id_euro:
                active_euro=True
            #raise UserError(_("valor usd=%s valor euro=%s")%(id_usd,id_euro)) 

            lista=self.env['res.company'].search([])
            #for det in lista:
            ##dolar=60
            vals=({
                        #'hora':datetime.now(),
                'name':datetime.now(),
                'inverse_company_rate':dolar,
                'currency_id':id_usd.id,
                'company_rate':1/dolar,
                'company_id':'', #det.id, #self.env.company.id #det.id,
                })
            self.create(vals)
            if active_euro==True:
                vals2=({
                            #'hora':datetime.now(),
                    'name':datetime.now(),
                    'inverse_company_rate':euro,
                    'currency_id':id_euro.id,
                    'company_rate':1/euro,
                    'company_id':'', #det.id, #self.env.company.id #det.id,
                    })
                self.create(vals2)
            self.funcion_actualiza_coste_precio_venta()

            

    def funcion_actualiza_coste_precio_venta(self):
        lista2=self.env['product.product'].search([])
        if lista2:
            for item in lista2:
                item.actualiza_coste()
                item.actualiza_precio_venta_bs()

        lista=self.env['product.template'].search([])
        if lista:
            for rec in lista:
                rec.actualiza_coste()
                rec.actualiza_precio_venta_bs()