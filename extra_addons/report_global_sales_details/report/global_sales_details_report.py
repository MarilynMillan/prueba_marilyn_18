from odoo import api, fields, models, _
from odoo.exceptions import UserError
from datetime import datetime, time
import pytz

class ReportGlobalSalesDetails(models.AbstractModel):
    _name = 'report.report_global_sales_details.report_template'
    _description = 'Reporte Global de Detalles de Ventas'

    @api.model
    def _get_report_values(self, docids, data=None):
        start_date_str = data.get('start_date')
        end_date_str = data.get('end_date')
        
        # 1. Convertimos el string a objeto Date
        start_date = fields.Date.from_string(start_date_str)
        end_date = fields.Date.from_string(end_date_str)
        
        # 2. Tomamos la zona horaria (America/Caracas)
        user_tz = pytz.timezone(self.env.user.tz or 'America/Caracas')
        
        # 3. Forzamos 00:00:00 para el inicio y 23:59:59 para el fin, convirtiendo a UTC (hora de la BD de Odoo)
        start_dt_utc = user_tz.localize(datetime.combine(start_date, time.min)).astimezone(pytz.utc).replace(tzinfo=None)
        end_dt_utc = user_tz.localize(datetime.combine(end_date, time.max)).astimezone(pytz.utc).replace(tzinfo=None)
        
        # 4. Convertimos a string para usarlo en el .search()
        search_start = fields.Datetime.to_string(start_dt_utc)
        search_end = fields.Datetime.to_string(end_dt_utc)
        
        company = self.env.company
        currency_usd_obj = self.env.ref('base.USD')

        # Tasa Promedio
        lista = self.env['res.currency.rate'].search([
            ('currency_id', '=', currency_usd_obj.id), 
            ('name', '>=', start_date), 
            ('name', '<=', end_date)
        ])
        
        if lista:
            suma = sum(det.inverse_company_rate for det in lista)
            tasa_promedio = suma / len(lista)
        else:
            tasa_promedio = 1.0

        pos_products_data = {}
        sale_products_data = {}
        payments_data = {}
        
        total_pos_bs = 0.0
        total_pos_usd = 0.0
        total_sale_bs = 0.0
        total_sale_usd = 0.0

        # --- POS Orders ---
        pos_orders = self.env['pos.order'].search([
            ('date_order', '>=', start_date_str),
            ('date_order', '<=', end_date_str),
            ('state', 'in', ['paid', 'done', 'invoiced'])
        ])

        for order in pos_orders:
            # En POS la moneda suele ser la base de la compañía, o order.currency_id
            for line in order.lines:
                categ_name = line.product_id.categ_id.name or 'Sin Categoría'
                product_name = line.product_id.name
                
                if categ_name not in pos_products_data:
                    pos_products_data[categ_name] = {}
                if product_name not in pos_products_data[categ_name]:
                    pos_products_data[categ_name][product_name] = {
                        'product_name': product_name,
                        'quantity': 0.0,
                        'uom': line.product_id.uom_id.name,
                        'price_total': 0.0,
                        'price_total_usd': 0.0
                    }
                
                amount_bs = line.price_subtotal_incl
                amount_usd = (amount_bs / tasa_promedio) if tasa_promedio else 0.0
                
                pos_products_data[categ_name][product_name]['quantity'] += line.qty
                pos_products_data[categ_name][product_name]['price_total'] += amount_bs
                pos_products_data[categ_name][product_name]['price_total_usd'] += amount_usd
                
                total_pos_bs += amount_bs
                total_pos_usd += amount_usd

            for payment in order.payment_ids:
                payment_name = payment.payment_method_id.name
                if payment_name not in payments_data:
                    payments_data[payment_name] = {'name': payment_name, 'total': 0.0, 'total_usd': 0.0}
                payments_data[payment_name]['total'] += payment.amount
                payments_data[payment_name]['total_usd'] += (payment.amount / tasa_promedio) if tasa_promedio else 0.0

        # --- Sale Orders ---
        sale_orders = self.env['sale.order'].search([
            ('date_order', '>=', start_date_str),
            ('date_order', '<=', end_date_str),
            ('state', 'in', ['sale', 'done']),
            ('invoice_status', '=', 'invoiced')
        ])
        
        processed_payment_ids = set()
        for order in sale_orders:
            
            # NUEVO: Extraer la tasa directamente de la orden de venta. 
            # Se usa un fallback a tasa_promedio o 1.0 por si alguna orden antigua no tiene el campo x_tasa lleno.
            tasa_orden = order.x_tasa if order.x_tasa and order.x_tasa > 0 else tasa_promedio
            
            for line in order.order_line:
                if not line.display_type:
                    categ_name = line.product_id.categ_id.name or 'Sin Categoría'
                    product_name = line.product_id.name
                    
                    if categ_name not in sale_products_data:
                        sale_products_data[categ_name] = {}
                    if product_name not in sale_products_data[categ_name]:
                        sale_products_data[categ_name][product_name] = {
                            'product_name': product_name,
                            'quantity': 0.0,
                            'uom': line.product_uom.name,
                            'price_total': 0.0,
                            'price_total_usd': 0.0
                        }
                    
                    # CORRECCIÓN: Usar 'tasa_orden' en lugar de 'tasa_promedio' para los cálculos
                    if order.currency_id == currency_usd_obj:
                        amount_usd = line.price_total
                        amount_bs = amount_usd * tasa_orden
                    elif order.currency_id == company.currency_id:
                        amount_bs = line.price_total
                        amount_usd = (amount_bs / tasa_orden) if tasa_orden else 0.0
                    else:
                        # Si es otra moneda rara, convertimos a Bs y luego calculamos a USD
                        amount_bs = order.currency_id._convert(line.price_total, company.currency_id, company, order.date_order)
                        amount_usd = (amount_bs / tasa_orden) if tasa_orden else 0.0
                    
                    sale_products_data[categ_name][product_name]['quantity'] += line.product_uom_qty
                    sale_products_data[categ_name][product_name]['price_total'] += amount_bs
                    sale_products_data[categ_name][product_name]['price_total_usd'] += amount_usd
                    
                    total_sale_bs += amount_bs
                    total_sale_usd += amount_usd

            # CORRECCIÓN PARA PAGOS: También debes ajustar el ciclo de pagos asociado a esta orden para que cuadre
            for invoice in order.invoice_ids.filtered(lambda inv: inv.state == 'posted' and inv.payment_state in ('in_payment', 'paid')):
                for payment in invoice._get_reconciled_payments():
                    if payment.id in processed_payment_ids:
                        continue
                    processed_payment_ids.add(payment.id)
                    
                    payment_name = payment.journal_id.name or 'Pago (Ventas)'
                    
                    # Usamos 'tasa_orden' para que el pago refleje la misma tasa que la venta
                    if payment.currency_id == currency_usd_obj:
                        amount_usd = payment.amount
                        amount_bs = amount_usd * tasa_orden
                    elif payment.currency_id == company.currency_id:
                        amount_bs = payment.amount
                        amount_usd = (amount_bs / tasa_orden) if tasa_orden else 0.0
                    else:
                        amount_bs = payment.currency_id._convert(payment.amount, company.currency_id, company, payment.date)
                        amount_usd = (amount_bs / tasa_orden) if tasa_orden else 0.0
                    
                    if payment_name not in payments_data:
                        payments_data[payment_name] = {'name': payment_name, 'total': 0.0, 'total_usd': 0.0}
                    
                    payments_data[payment_name]['total'] += amount_bs
                    payments_data[payment_name]['total_usd'] += amount_usd
                
        # Format products list WITH subtotals
        formatted_pos_products = []
        for categ, prods in pos_products_data.items():
            cat_qty = sum(p['quantity'] for p in prods.values())
            cat_bs = sum(p['price_total'] for p in prods.values())
            cat_usd = sum(p['price_total_usd'] for p in prods.values())
            
            formatted_pos_products.append({
                'name': categ,
                'products': list(prods.values()),
                'subtotal_qty': cat_qty,
                'subtotal_bs': cat_bs,
                'subtotal_usd': cat_usd,
            })
            
        formatted_sale_products = []
        for categ, prods in sale_products_data.items():
            cat_qty = sum(p['quantity'] for p in prods.values())
            cat_bs = sum(p['price_total'] for p in prods.values())
            cat_usd = sum(p['price_total_usd'] for p in prods.values())
            
            formatted_sale_products.append({
                'name': categ,
                'products': list(prods.values()),
                'subtotal_qty': cat_qty,
                'subtotal_bs': cat_bs,
                'subtotal_usd': cat_usd,
            })
            
        formatted_payments = list(payments_data.values())

        return {
            'date_start': start_date_str,
            'date_stop': end_date_str,
            'company': company,
            'currency_usd_obj': currency_usd_obj,
            'pos_products': formatted_pos_products,
            'sale_products': formatted_sale_products,
            'payments': formatted_payments,
            'tasa_promedio': tasa_promedio,
            'total_pos_bs': total_pos_bs,
            'total_pos_usd': total_pos_usd,
            'total_sale_bs': total_sale_bs,
            'total_sale_usd': total_sale_usd,
            'total_general_bs': total_pos_bs + total_sale_bs,
            'total_general_usd': total_pos_usd + total_sale_usd,
        }
