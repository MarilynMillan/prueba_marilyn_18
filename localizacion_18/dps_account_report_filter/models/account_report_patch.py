from odoo import models
from odoo.addons.account_reports.models import account_report

def patched_set_xlsx_cell_sizes(self, sheet, fonts, x, y, value, style, is_merged=False):
    # En Odoo 18, el redimensionamiento automático suele estar integrado 
    # o se maneja a través de otros atributos. 
    # Este parche asegura que no falle si col_sizes no existe.
    
    col = x
    row = y

    # Obtenemos los diccionarios de forma segura. Si no existen, usamos un dict vacío.
    col_sizes = getattr(sheet, 'col_sizes', {})
    row_sizes = getattr(sheet, 'row_sizes', {})

    # Intentamos obtener el ancho actual, por defecto 8.43 (estándar de Excel)
    col_width_data = col_sizes.get(col, [8.43])
    col_width = col_width_data if isinstance(col_width_data, (float, int)) else col_width_data[0]

    if value:
        value_str = str(value)
        # Lógica simple para calcular ancho basado en el largo del texto
        content_width = len(value_str) + 2 

        # Solo intentamos escribir en col_sizes si el objeto sheet lo permite
        if col_width < content_width and hasattr(sheet, 'col_sizes'):
            sheet.col_sizes[col] = [content_width]

    # Lo mismo para las filas
    if hasattr(sheet, 'row_sizes') and row not in sheet.row_sizes:
        sheet.row_sizes[row] = 15

# Aplicar el Monkey patch al método original
account_report.AccountReport._set_xlsx_cell_sizes = patched_set_xlsx_cell_sizes
