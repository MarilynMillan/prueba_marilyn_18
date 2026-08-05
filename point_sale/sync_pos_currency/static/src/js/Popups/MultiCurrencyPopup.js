/** @odoo-module **/

import { Dialog } from "@web/core/dialog/dialog";
import { Component, useState } from "@odoo/owl";
import { useService } from "@web/core/utils/hooks";

export class MultiCurrencyPopup extends Component {
    static components = { Dialog };
    static template = "sync_pos_currency.MultiCurrencyPopup";


    static props = {
        close: Function,
        title: { type: String, optional: true },
        confirm: { type: Function, optional: true },
        cancel: { type: Function, optional: true },
        payment_method: { type: Array, optional: true },
        getPayload: { type: Function, optional: true },
    };


    static defaultProps = {
        title: "Multi-Currency Payment",
    };

    setup() {
        const multicurrencies = this.env.services.pos.multicurrencypayment || [];
        if (multicurrencies.length === 0) {
            console.error("No multi-currency data available!");
        }
        this.dialog = useService("dialog");
        this.state = useState({
            values: multicurrencies,
            default_currency: this.env.services.pos.currency,
            selected_curr_name: multicurrencies[0]?.name || "",
            selected_rate: multicurrencies[0]?.rate || 0,
            inverse_rate: multicurrencies[0]?.inverse_rate || 0,
            symbol: multicurrencies[0]?.symbol || "",
            AmountTotal: this.getDueAmount(),
            amount_total_currency: 0,
        });

        if (this.env.services.pos.config.cash_rounding) {
            const cash_rounding = this.env.services.pos.cash_rounding[0]?.rounding || 1;
            this.state.AmountTotal = this.roundPr(this.env.services.pos.get_order().get_due(), cash_rounding);
        }

        this.state.amount_total_currency = this.calculateTotalCurrency();
    }

    getDueAmount() {
        return this.env.services.pos.get_order().get_due();
    }

    calculateTotalCurrency() {
        return (this.state.selected_rate * this.state.AmountTotal).toFixed(4);
    }

    onCurrencyChange(event) {
        const selectedValue = this.state.values.find((val) => val.id === parseFloat(event.target.value));
        if (selectedValue) {
            this.state.selected_curr_name = selectedValue.name;
            this.state.selected_rate = selectedValue.rate;
            this.state.inverse_rate = selectedValue.inverse_rate;
            this.state.symbol = selectedValue.symbol;
            this.state.amount_total_currency = this.calculateTotalCurrency();
        }
    }

    roundPr(value, rounding) {
        return Math.round(value / rounding) * rounding;
    }

    confirm() {
        const payload = this.getPayload ? this.getPayload() : {
            currency_name: this.state.selected_curr_name,
            selected_rate: this.state.selected_rate,
            inverse_rate: this.state.inverse_rate,
            symbol: this.state.symbol,
        };
        this.props.confirm({ confirmed: true, payload });
        this.props.close();
    }


    cancel() {
        if (this.props.cancel) {
            this.props.cancel();
        } else {
            this.props.close();
        }
    }

    getPayload() {
        return {
            currency_name: this.state.selected_curr_name,
            selected_rate: this.state.selected_rate,
            inverse_rate: this.state.inverse_rate,
            symbol: this.state.symbol,
        };
    }
}
