/** @odoo-module **/

import { patch } from '@web/core/utils/patch';
import { ProductScreen } from '@point_of_sale/app/screens/product_screen/product_screen';


patch(ProductScreen.prototype, {
    getCurrencyDual(amt) {
        var amount = amt * (
            this.pos.config.second_currency_rate / this.pos.config.company_rate
        )
        return `${this.pos.config.second_currency_symbol} ${amount.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`;
    },
});



