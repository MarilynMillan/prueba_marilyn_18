from odoo import models, fields, api, _
from odoo.exceptions import UserError

class PosDetailsWizardInherit(models.TransientModel):
    _inherit = 'pos.details.wizard'

    def generate_report(self):
        action = super(PosDetailsWizardInherit, self).generate_report()
        report_data = action.get('data', {})
        rate_base_to_usd=self.tasa_promedio()
        if report_data:
            company = self.env.company
            currency_base = company.currency_id 
            currency_usd_obj = self.env.ref('base.USD') 
            rate_date = fields.Datetime.to_datetime(self.start_date)

            try:
                """rate_base_to_usd = currency_base._get_conversion_rate(
                    currency_base, 
                    currency_usd_obj, 
                    company, 
                    rate_date
                )"""
                
            except Exception:
                raise UserError(_(
                    "No se pudo obtener la tasa de cambio de %s a USD para la fecha %s. "
                    "Asegúrese de que la tasa esté configurada en Contabilidad > Monedas." 
                    % (currency_base.name, rate_date.strftime('%Y-%m-%d'))
                ))
            
            # INYECTAMOS LA TASA Y LA PRECISION DE LA MONEDA USD
            report_data['currency_usd_symbol'] = currency_usd_obj.symbol
            report_data['currency_usd_precision'] = currency_usd_obj.decimal_places
            report_data['rate_base_to_usd'] = rate_base_to_usd
            
        return action

    def tasa_promedio(self):
        cont=suma=0
        tasa_prom=1
        lista=self.env['res.currency.rate'].search([('name','>=',self.start_date),('name','<=',self.end_date)])
        if lista:
            for det in lista:
                suma=suma+det.inverse_company_rate
                cont=cont+1
        tasa_prom=suma/cont
        return tasa_prom

