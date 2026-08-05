/** @odoo-module **/

import { patch } from '@web/core/utils/patch';
import { usePos } from '@point_of_sale/app/store/pos_hook'
import { OrderReceipt } from '@point_of_sale/app/screens/receipt_screen/receipt/order_receipt';

patch(OrderReceipt.prototype, {

    setup() {
		this.pos = usePos();
	},

    formatCurrencyDual(amount) {
        var amt = amount * (
            this.pos.config.second_currency_rate / this.pos.config.company_rate
        )
        return `${this.pos.config.second_currency_symbol} ${amt.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`;
    },
});