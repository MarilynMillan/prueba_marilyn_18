/** @odoo-module **/

import { PaymentScreen } from "@point_of_sale/app/screens/payment_screen/payment_screen";
import { registry } from "@web/core/registry";
import { WarningDialog } from "@web/core/errors/error_dialogs";
import { patch } from "@web/core/utils/patch";
import { useService } from "@web/core/utils/hooks";
import { MultiCurrencyPopup } from "../Popups/MultiCurrencyPopup"
import { makeAwaitable } from "@point_of_sale/app/store/make_awaitable_dialog";
import { _t } from "@web/core/l10n/translation";
import { ConfirmationDialog } from "@web/core/confirmation_dialog/confirmation_dialog";

patch(PaymentScreen.prototype, {
    setup() {
        super.setup(...arguments);
        this.dialog = useService("dialog");
    },
    async payMultipleCurrencyClickHandler() {
        if (this.pos.multicurrencypayment.length > 0) {
            const payment_method_data = this.payment_methods_from_config.map((id) => id);
            const dialogPopup = await makeAwaitable(this.dialog, MultiCurrencyPopup, {
                payment_method: payment_method_data,
                title: _t("Choose Currency"),
                confirm: async ({ confirmed, payload }) => {
                    if (confirmed) {
                        const enteredAmount = parseFloat(document.querySelector('.pay_amount').value || 0);
                        if (enteredAmount > 0) {
                            const paymentMethodId = parseInt(document.querySelector('.payment-method-select').value);
                            const amountInBaseCurrency = enteredAmount / payload.selected_rate;
                            if (this.pos.config.cash_rounding) {
                                const cashRounding = this.pos.cash_rounding[0]?.rounding || 1;
                                amountInBaseCurrency = this.roundPr(amountInBaseCurrency, cash_rounding);
                            }
                            const paymentMethodSelected = this.payment_methods_from_config.find(
                                (method) => method.id === paymentMethodId
                            );
                            const paymentLine = this.currentOrder.add_paymentline(paymentMethodSelected);
                            paymentLine.set_amount(amountInBaseCurrency);
                            paymentLine.currency_amount_total = enteredAmount;
                            paymentLine.selected_currency = payload.currency_name;
                            paymentLine.selected_currency_symbol = payload.symbol;

                        } else {
                            this.dialog.add(ConfirmationDialog, {
                                title: _t("Amount Not Added"),
                                body: _t("Please Enter the Amount!"),
                            });
                        }
                    }
                },
            });
        } else {
            this.dialog.add(ConfirmationDialog, {
                title: _t("Currency Not Configured"),
                body: _t("Please Configure The Currency For Multi-Currency Payment."),
            });
        }
    }
})
