from odoo import models, _, api
import datetime

NUMBER_FIGURE_TYPES = ('float', 'integer', 'monetary', 'percentage')

class AccountReport(models.Model):
    _inherit = 'account.report'

    def _get_line_info(self, line_id):
        # Odoo 18 usa IDs como 'account.general.ledger.line_account.move.line_12345'
        if not line_id or not isinstance(line_id, str):
            return {}
        try:
            # Buscamos el ID numérico que está al final de la cadena
            import re
            match = re.search(r'(\d+)$', line_id)
            if match:
                return {'res_id': int(match.group(1))}
        except Exception:
            pass
        return {}

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

        company_currency = self.env.company.currency_id
        to_currency_name = options.get('selected_currencies') if options else None
        to_currency = self.env['res.currency'].search([('name', '=', to_currency_name)], limit=1) if to_currency_name else None
        
        col_group_key = col_data.get('column_group_key') if col_data else None
        expr_label = col_data.get('expression_label') or (column_expression.label if column_expression else '')
        res_currency = currency or to_currency or company_currency

        if isinstance(col_value, (int, float)) and col_value != 0:
            is_monetary_col = expr_label in ('debit', 'credit', 'balance')
            
            if to_currency and to_currency.name == 'USD' and is_monetary_col:
                rate = 0
                
                # 1. Intentar por ID (Válido para cualquier reporte)
                line_info = self._get_line_info(report_line_id)
                res_id = line_info.get('res_id')
                if res_id:
                    aml = self.env['account.move.line'].browse(res_id)
                    if aml.exists() and 'tasa' in aml.move_id._fields:
                        rate = aml.move_id.tasa

                # 2. SOLO USAR busca_tasa si es LIBRO MAYOR (o reportes de detalle)
                # Odoo identifica las líneas del Libro Mayor con strings que contienen estos términos
                report_line_str = str(report_line_id).lower()
                es_libro_mayor = 'general_ledger' in report_line_str or 'account.move.line' in report_line_str
                
                if rate <= 0 and es_libro_mayor:
                    # Aquí es donde usamos tu función solo si estamos en el detalle del Mayor
                    rate = self.busca_tasa(col_value)

                # 3. Aplicar conversión
                if rate > 0:
                    # Dividimos el valor original (Bs) entre la tasa encontrada (Manual o Buscada)
                    col_value = col_value / rate
                else:
                    # PARA BALANCE GENERAL / P&L / RESÚMENES:
                    # Si no hubo ID y no es Libro Mayor, usamos la conversión nativa de Odoo
                    date_to = options.get('date', {}).get('date_to') or fields.Date.today()
                    rate = self.busca_tasa(col_value)
                    if rate==1:
                        col_value = company_currency._convert(col_value, to_currency, self.env.company, date_to)
                    else:
                        col_value = col_value/rate
                
                res_currency = to_currency

            elif expr_label == 'amount_currency':
                usd = self.env['res.currency'].search([('name', '=', 'USD')], limit=1)
                res_currency = usd or res_currency

        # --- RETORNO SEGURO ---
        col_data = col_data or {}
        column_expression = column_expression or self.env['account.report.expression']
        figure_type = column_expression.figure_type or col_data.get('figure_type', 'string')
        format_params = {'currency_id': res_currency.id} if figure_type == 'monetary' and res_currency else {}

        return {
            'auditable': col_value is not None and column_expression.auditable,
            'blank_if_zero': column_expression.blank_if_zero or col_data.get('blank_if_zero', False),
            'column_group_key': col_group_key,
            'currency': res_currency.id if res_currency else None,
            'currency_symbol': res_currency.symbol if res_currency else None,
            'digits': digits,
            'expression_label': expr_label,
            'figure_type': figure_type,
            'green_on_positive': column_expression.green_on_positive if column_expression else False,
            'has_sublines': has_sublines,
            'is_zero': col_value is None or (isinstance(col_value, (int, float)) and self._is_value_zero(col_value, figure_type, format_params)),
            'no_format': col_value,
            'format_params': format_params,
            'report_line_id': report_line_id,
            'sortable': col_data.get('sortable', False),
            'comparison_mode': col_data.get('comparison_mode'),
        }


    def busca_tasa(self, valor):
        """ Busca la tasa en account.move.line basada en el monto (balance) """
        tasa = 1
        try:
            val = float(valor)
            if val == 0:
                return 1
            
            # Buscamos por balance positivo o negativo
            busca = self.env['account.move.line'].search([
                '|', 
                ('balance', '=', val), 
                ('balance', '=', -val)
            ], limit=1)
            
            if busca and 'tasa' in busca.move_id._fields:
                if busca.move_id.tasa > 0:
                    tasa = busca.move_id.tasa
        except:
            pass
        return tasa


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