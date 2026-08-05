from odoo import api, fields, models, _
from datetime import date, timedelta, datetime
from bs4 import BeautifulSoup
import requests
import urllib3
urllib3.disable_warnings()
class ResCurrency(models.Model):
    _inherit = 'res.currency'

    

    def get_trm_systray(self):
        company_id = self.env.company
        rates = company_id.currency_id_dif._get_rates(company_id, date.today())
        rates = 1 / rates[company_id.currency_id_dif.id]
        decimal_dual_currency_rate = self.env['decimal.precision'].precision_get('Dual_Currency_rate')
        if rates:
            rates = round(rates, decimal_dual_currency_rate if decimal_dual_currency_rate else 2)
        else:
            rates = 0
        return rates