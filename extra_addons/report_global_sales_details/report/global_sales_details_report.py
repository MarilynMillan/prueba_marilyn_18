from odoo import api, fields, models, _
from odoo.exceptions import UserError
import pytz

class ReportGlobalSalesDetails(models.AbstractModel):
    _name = 'report.report_global_sales_details.report_global_sales_details_template'
    _description = 'Reporte Global de Detalles de Ventas'

    @api.model
    def _get_report_values(self, docids, data=None):
        start_date_str = data.get('start_date')
        end_date_str = data.get('end_date')
        
        start_date = fields.Datetime.from_string(start_date_str)
        end_date = fields.Datetime.from_string(end_date_str)
        
        company = self.env.company
        currency_usd_obj = self.env.ref('base.USD')

        # Tasa Promedio
        lista = self.env['res.currency.rate'].search([
            ('currency_id', '=', currency_usd_obj.id), 
            ('name', '>=', start_date.date()), 
            ('name', '<=', end_date.date())
        ])
        
        if lista:
            suma = sum(det.inverse_company_rate for det in lista)
            tasa_promedio = suma / len(lista)
        else:
            tasa_promedio = 1.0

        products_data = {}
        payments_data = {}

        # --- POS Orders ---
        pos_orders = self.env['pos.order'].search([
            ('date_order', '>=', start_date_str),
            ('date_order', '<=', end_date_str),
            ('state', 'in', ['paid', 'done', 'invoiced'])
        ])

        for order in pos_orders:
            for line in order.lines:
                categ_name = line.product_id.categ_id.name or 'Sin Categoría'
                product_name = line.product_id.name
                
                if categ_name not in products_data:
                    products_data[categ_name] = {}
                if product_name not in products_data[categ_name]:
                    products_data[categ_name][product_name] = {
                        'product_name': product_name,
                        'quantity': 0.0,
                        'uom': line.product_id.uom_id.name,
                        'price_total': 0.0,
                        'price_total_usd': 0.0
                    }
                
                products_data[categ_name][product_name]['quantity'] += line.qty
                products_data[categ_name][product_name]['price_total'] += line.price_subtotal_incl
                products_data[categ_name][product_name]['price_total_usd'] += (line.price_subtotal_incl / tasa_promedio) if tasa_promedio else 0.0

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
            ('state', 'in', ['sale', 'done'])
        ])

        # Track processed payments globally to avoid double counting across multiple invoices/orders
        processed_payment_ids = set()

        for order in sale_orders:
            for line in order.order_line:
                if not line.display_type:  # Ignore sections and notes
                    categ_name = line.product_id.categ_id.name or 'Sin Categoría'
                    product_name = line.product_id.name
                    
                    if categ_name not in products_data:
                        products_data[categ_name] = {}
                    if product_name not in products_data[categ_name]:
                        products_data[categ_name][product_name] = {
                            'product_name': product_name,
                            'quantity': 0.0,
                            'uom': line.product_uom.name,
                            'price_total': 0.0,
                            'price_total_usd': 0.0
                        }
                    
                    price_company_curr = order.currency_id._convert(line.price_total, company.currency_id, company, order.date_order)
                    
                    products_data[categ_name][product_name]['quantity'] += line.product_uom_qty
                    products_data[categ_name][product_name]['price_total'] += price_company_curr
                    products_data[categ_name][product_name]['price_total_usd'] += (price_company_curr / tasa_promedio) if tasa_promedio else 0.0

            # Find related payments via invoices
            for invoice in order.invoice_ids.filtered(lambda inv: inv.state == 'posted' and inv.payment_state in ('in_payment', 'paid')):
                # In Odoo, _get_reconciled_payments() returns account.payment records
                for payment in invoice._get_reconciled_payments():
                    if payment.id in processed_payment_ids:
                        continue
                    processed_payment_ids.add(payment.id)
                    
                    payment_name = payment.journal_id.name or 'Pago (Ventas)'
                    
                    # We should technically use the partial amount reconciled with this invoice
                    # But if we track by payment_id we just take the total payment amount once per order
                    amount_company_curr = payment.currency_id._convert(payment.amount, company.currency_id, company, payment.date)
                    
                    if payment_name not in payments_data:
                        payments_data[payment_name] = {'name': payment_name, 'total': 0.0, 'total_usd': 0.0}
                    
                    payments_data[payment_name]['total'] += amount_company_curr
                    payments_data[payment_name]['total_usd'] += (amount_company_curr / tasa_promedio) if tasa_promedio else 0.0
                
        # Format products list
        formatted_products = []
        for categ, prods in products_data.items():
            formatted_products.append({
                'name': categ,
                'products': list(prods.values())
            })
            
        formatted_payments = list(payments_data.values())

        return {
            'date_start': start_date_str,
            'date_stop': end_date_str,
            'company': company,
            'currency_usd_obj': currency_usd_obj,
            'products': formatted_products,
            'payments': formatted_payments,
            'tasa_promedio': tasa_promedio
        }
