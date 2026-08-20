from odoo import models, fields, api

class GlobalSalesDetailsWizard(models.TransientModel):
    _name = 'global.sales.details.wizard'
    _description = 'Global Sales Details Wizard'

    start_date = fields.Date(string='Desde', required=True, default=fields.Date.context_today)
    end_date = fields.Date(string='Hasta', required=True, default=fields.Date.context_today)

    def generate_report(self):
        data = {
            'start_date': fields.Date.to_string(self.start_date),
            'end_date': fields.Date.to_string(self.end_date),
        }
        return self.env.ref('report_global_sales_details.action_report_global_sales').report_action([], data=data)
