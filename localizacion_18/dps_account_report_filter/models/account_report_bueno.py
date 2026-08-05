from odoo import models, _, api
import datetime

NUMBER_FIGURE_TYPES = ('float', 'integer', 'monetary', 'percentage')

class AccountReport(models.Model):
    _inherit = 'account.report'

    def _init_options_currencies(self, options, previous_options=None):
        currencies = self.env['res.currency'].search([])
        options['currencies'] = [{'id': c.id, 'name': _(c.name)} for c in currencies]

        selected_currency_id = previous_options.get('selected_currencies_id')
        selected_currency_name = previous_options.get('selected_currencies')

        if selected_currency_id:
            options['selected_currencies'] = self.env['res.currency'].browse(selected_currency_id).name
        else:
            options['selected_currencies'] = selected_currency_name or self.env.company.currency_id.name


    def _build_column_dict(self, col_value, col_data, options=None, currency=False, digits=1,
                           column_expression=None, has_sublines=False, report_line_id=None):
        if col_value is None and col_data is None:
            return {}

        date_obj = datetime.datetime.strptime(options['date']['date_to'], '%Y-%m-%d').date()
        company_currency = self.env.company.currency_id
        
        # Moneda seleccionada en tu filtro (ej. USD o VEF)
        to_currency_name = options.get('selected_currencies')
        to_currency = self.env['res.currency'].search([('name', '=', to_currency_name)], limit=1)

        # Identificar la columna por su etiqueta técnica en Odoo 18
        expr_label = column_expression.label if column_expression else ''
        
        # Forzamos la detección: ¿Es la columna donde va el monto original del asiento?
        is_amount_currency_col = (expr_label == 'amount_currency' or col_data.get('expression_label') == 'amount_currency')

        # Moneda para el formato de esta celda
        res_currency = currency or to_currency or company_currency

        if isinstance(col_value, (int, float)):
            if is_amount_currency_col:
                # --- AQUÍ ESTÁ EL TRUCO ---
                # Si estamos en esta columna, NO permitimos que Odoo convierta el valor.
                # Intentamos recuperar el símbolo $ buscando cualquier moneda que no sea la local.
                if not currency or currency == company_currency:
                    usd = self.env['res.currency'].search([('name', '=', 'USD')], limit=1)
                    res_currency = usd or res_currency
                # No hacemos nada con col_value, lo dejamos como viene de la base de datos (500.00)
                pass
            else:
                # Columnas Debe, Haber y Balance: Conversión obligatoria
                if to_currency and to_currency != company_currency:
                    col_value = company_currency._convert(col_value, to_currency, date=date_obj)
                    res_currency = to_currency

        col_data = col_data or {}
        column_expression = column_expression or self.env['account.report.expression']
        figure_type = column_expression.figure_type or col_data.get('figure_type', 'string')
        
        # Aseguramos que el format_params use la moneda que decidimos
        format_params = {'currency_id': res_currency.id} if res_currency else {}
        if figure_type in ('float', 'percentage'):
            format_params['digits'] = digits

        return {
            'auditable': col_value is not None and column_expression.auditable,
            'blank_if_zero': column_expression.blank_if_zero or col_data.get('blank_if_zero', False),
            'column_group_key': col_data.get('column_group_key'),
            'currency': res_currency.id if res_currency else None,
            'currency_symbol': res_currency.symbol if res_currency else None,
            'digits': digits,
            'expression_label': expr_label,
            'figure_type': figure_type,
            'is_zero': col_value is None or (isinstance(col_value, (int, float)) and self._is_value_zero(col_value, figure_type, format_params)),
            'no_format': col_value,
            'format_params': format_params,
            'report_line_id': report_line_id,
            'sortable': col_data.get('sortable', False),
        }



    # Mantener el resto de las funciones de redondeo igual...
    def _init_options_rounding_unit(self, options, previous_options=None):
        options['rounding_unit'] = previous_options.get('rounding_unit', 'decimals') if previous_options else 'decimals'
        currency_name = previous_options.get('selected_currencies') or self.env.company.currency_id.name
        currency_obj = self.env['res.currency'].search([('name', '=', currency_name)], limit=1) or self.env.company.currency_id
        options['rounding_unit_names'] = self._get_rounding_unit_names(currency_obj)

    def _get_rounding_unit_names(self, currency_obj):
        currency_symbol = currency_obj.symbol or self.env.company.currency_id.symbol
        return {
            'decimals': f'.{currency_symbol}',
            'units': f'U {currency_symbol}',
            'thousands': f'K{currency_symbol}',
            'millions': f'M{currency_symbol}',
        }