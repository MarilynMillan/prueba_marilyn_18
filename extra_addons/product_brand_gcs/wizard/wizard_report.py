from datetime import datetime, timedelta
from odoo.tools.misc import DEFAULT_SERVER_DATE_FORMAT

from odoo import models, fields, api, _, tools
from odoo.exceptions import UserError
import logging

import io
from io import BytesIO

import xlsxwriter
import shutil
import base64
import csv
import xlwt

_logger = logging.getLogger(__name__)


class WizardCommiones(models.TransientModel):
    _name = "wizard.report.balanza"

    state = fields.Selection([('choose', 'choose'), ('get', 'get')], default='choose')
    report = fields.Binary('Prepared file', filters='.xls', readonly=True)
    name = fields.Char('File Name', size=32)
    company_id = fields.Many2one('res.company','Company',default=lambda self: self.env.company.id)



    def print_txp_2(self):
        self.ensure_one()
        output_lines = []
        
        products = self.env['product.template'].search([('product_pesaje', '=', True)])
        raise UserError(_("aqui"))
        for product in products:
            # Campos en el orden del manual de la RLS1100
            plu_num = str(product.lf_code or '0')
            plu_name = product.name.replace('"', '')
            impuesto=product.taxes_id.amount
            precio_con_iva=33333 #round((product.list_price*impuesto/100)+product.list_price,4)
            unit_price = int(precio_con_iva * 100)
            formatted_price = f"{unit_price:07d}"
            tare = str(product.tare or '0')
            unit_price_unit = '4' # Valor por defecto
            life_time = str(product.shelf_time or '0')
            package_time = '0' # Valor por defectoit 
            department_no = str(product.deptment or '0')
            barcode_type = str(product.pbarcode or '0')
            barcode = str(product.default_code or '0').zfill(13)
            fix_weight = str(product.fix_weight or '0')
            fix_price = int(precio_con_iva * 100)
            formatted_fix_price = f"{fix_price:07d}"
            unit_of_measure = str(product.weight_unit or '0')
            message_no = str(product.message1 or '0')
            label_format_no = '0' # Valor por defecto
            batch = '0' # Valor por defecto
            reserved = '0' # Valor por defecto

            data = [
                plu_num, plu_name, formatted_price, tare, unit_price_unit,
                life_time, package_time, department_no, barcode_type, barcode,
                fix_weight, formatted_fix_price, unit_of_measure, message_no,
                label_format_no, batch, reserved
            ]

            # Construye la línea con el formato correcto, con tabulaciones y comillas
            line = '\t'.join([
                data[0], f'"{data[1]}"', data[2], data[3], data[4], data[5],
                data[6], data[7], data[8], data[9], data[10], data[11],
                data[12], data[13], data[14], data[15], data[16]
            ])
            output_lines.append(line)
        
        file_content = '\r\n'.join(output_lines).encode('utf-8')
        
        filename = 'plu.txp'
        self.write({
            'state': 'get',
            'report': base64.encodebytes(file_content),
            'name': filename
        })
        
        return {
            'name': 'Archivo de Balanza',
            'type': 'ir.actions.act_window',
            'res_model': 'wizard.report.balanza',
            'view_mode': 'form',
            'view_type': 'form',
            'res_id': self.id,
            'target': 'new'
        }


    def print_txp(self):
        self.ensure_one()
        output_lines = []
        
        # Obtener los productos que cumplen la condición
        products = self.env['product.template'].search([('product_pesaje', '=', True)])
        
        for product in products:
            # Preparar los datos para la línea del archivo TXP
            # La lista se ha modificado para incluir la primera columna con el valor fijo '0'.
            impuesto=product.taxes_id.amount if product.taxes_id else 0
            precio_con_iva=round((product.list_price*impuesto/100)+product.list_price,4)
            # Aseguramos que product.barcode exista antes de aplicar el corte [0:7]
            barcode_7_digitos = product.barcode[:7] if product.barcode else ''
            data = [
                0, # Columna fija con el valor 0
                product.name,  # 1
                product.lf_code,   # LF_code
                barcode_7_digitos, # code
                product.pbarcode,  # barcode
                f"{int(precio_con_iva*1000):07d}", # precio:unitario
                ##unit_price = int(product.list_price * 100)
                ##formatted_price = f"{unit_price:07d}"
                #'', # Columna vacía según el Excel
                product.weight_unit, # weight_unit 
                product.deptment, # deptment
                0.000, # weight_unit, # Repetido
                product.tare, # tare
                product.shelf_time, # shelf_time
                0.000, #  weight_unit, # Repetido
                product.fix_unit, # fix_unit
                product.fix_weight, # fix_weight
                product.tolerance, # tolerance 
                product.message1, # message1
                product.message2, # message2
                product.account, # account
                product.multilabel, # multilabel
            ]
            
            # Formatear la línea con el formato TXP
            formatted_data = []
            for value in data:
                # Si el valor es una cadena y contiene espacios, se encierra entre comillas dobles
                if isinstance(value, str) and ' ' in value:
                    formatted_data.append(f'"{value}"')
                # Si es un campo numérico con decimales, se formatea a 3 decimales
                elif isinstance(value, (float, int)):
                    formatted_data.append("{:.3f}".format(value) if isinstance(value, float) else str(value))
                # Si es None o False, se deja vacío, si no, se convierte a cadena
                elif value is False or value is None:
                    formatted_data.append('')
                else:
                    formatted_data.append(str(value))
                    
            output_lines.append('\t'.join(formatted_data))
            
        file_content = '\r\n'.join(output_lines).encode('utf-8')
        
        # Guardar el archivo en el registro del wizard
        filename = 'plu.txp'
        self.write({
            'state': 'get',
            'report': base64.encodebytes(file_content),
            'name': filename
        })
        
        return {
            'name': 'Archivo de Balanza',
            'type': 'ir.actions.act_window',
            'res_model': 'wizard.report.balanza',
            'view_mode': 'form',
            'view_type': 'form',
            'res_id': self.id,
            'target': 'new'
        }

    def generate_xls(self):
        """
        Genera un archivo Excel con los datos de los productos de la balanza
        y ajusta el ancho de las columnas automáticamente.
        """
        self.ensure_one()
        fp = BytesIO()
        workbook = xlsxwriter.Workbook(fp, {'in_memory': True})
        
        # Formatos para el excel
        header_format = workbook.add_format({'bold': True, 'align': 'center', 'valign': 'vcenter'})
        cell_format = workbook.add_format({'align': 'center', 'valign': 'vcenter'})
        
        # Creación de la hoja de cálculo
        sheet = workbook.add_worksheet('Datos Balanza')
        
        # Escribir la primera línea del encabezado sin formato
        sheet.write(0, 0, 'C:\\LB-MNV\\bin\\plu.txp')

        # Encabezados de la tabla sin la columna vacía
        headers = ['Name', 'LFCode', 'Code', 'BarCode', 'UnitPrice', 'WeightUnit', 'Deptment', 'WeightUnit', 'Tare', 'ShlefTime', 'WeightUnit', 'FixUnit', 'FixWeight', 'Tolerance', 'Message1', 'Message2', 'Account', 'MultiLabel']
        row = 1
        for col_idx, header_name in enumerate(headers):
            sheet.write(row, col_idx, header_name, header_format)
            
        row += 1
        
        # Obtener los productos que cumplen la condición
        products = self.env['product.template'].search([('product_pesaje', '=', True)])
        
        # Diccionario para almacenar el ancho máximo de cada columna
        max_col_widths = {i: len(headers[i]) for i in range(len(headers))}

        # Escribir los datos y calcular el ancho
        for product in products:
            col_data = [
                product.name,
                product.lf_code,
                product.default_code,
                product.pbarcode,
                product.list_price,
                product.weight_unit,
                product.deptment,
                product.weight_unit, # Repetido
                product.tare,
                product.shelf_time,
                product.weight_unit, # Repetido
                product.fix_unit,
                product.fix_weight,
                product.tolerance,
                product.message1,
                product.message2,
                product.account,
                product.multilabel,
            ]
            
            for col_idx, value in enumerate(col_data):
                # Usar el valor original si no es False o None
                cell_value = value if value is not False and value is not None else ''
                
                sheet.write(row, col_idx, cell_value, cell_format)
                
                # Actualizar el ancho máximo de la columna
                max_col_widths[col_idx] = max(max_col_widths[col_idx], len(str(cell_value)))
            
            row += 1
            
        # Ajustar el ancho de las columnas
        for col_idx, width in max_col_widths.items():
            sheet.set_column(col_idx, col_idx, width + 2)
            
        workbook.close()
        
        # Guardar el archivo en el registro del wizard
        filename = 'Archivo_Balanza.xlsx'
        self.write({
            'state': 'get',
            'report': base64.encodebytes(fp.getvalue()),
            'name': filename
        })
        
        return {
            'name': 'Archivo de Balanza',
            'type': 'ir.actions.act_window',
            'res_model': 'wizard.report.balanza',
            'view_mode': 'form',
            'view_type': 'form',
            'res_id': self.id,
            'target': 'new'
        }