from odoo import models, fields, api

class GlobalSalesDetailsWizard(models.TransientModel):
    _name = 'global.sales.details.wizard'
    _description = 'Global Sales Details Wizard'

    start_date = fields.Datetime(string='Start Date', required=True, default=fields.Datetime.now)
    end_date = fields.Datetime(string='End Date', required=True, default=fields.Datetime.now)

    def generate_report(self):
        data = {
            'start_date': fields.Datetime.to_string(self.start_date),
            'end_date': fields.Datetime.to_string(self.end_date),
        }
        return self.env.ref('report_global_sales_details.action_report_global_sales_details').report_action([], data=data)
