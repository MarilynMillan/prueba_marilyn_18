/** @odoo-module **/

import { patch } from "@web/core/utils/patch";
import { ReceiptScreen } from "@point_of_sale/app/screens/receipt_screen/receipt_screen";
import { usePos } from "@point_of_sale/app/store/pos_hook";
import { useService } from "@web/core/utils/hooks";
import { registry } from "@web/core/registry";

console.log("validando que este archivo se cargue")



patch(ReceiptScreen.prototype, {
    setup() {
        super.setup.call(this, ...arguments);
        this.pos = usePos();
        console.log("POS data:", this.pos);
        
    },

    ImprimirFiscal() {
        const order = this.currentOrder;
        console.log(order);

        if (!order) {
            console.error("No order found.");
            return;
        }

        if (!order.lines || order.lines.length === 0) {
            console.error("No order lines found.");
            return;
        }

        var lineas = [];
        var payment_order_lines = [];

        const client = order.get_partner(); // Cambia a get_partner() si es necesario
        if (client) {
            console.log("Cliente asociado:", client);
        } else {
            console.error("No client associated with the order.");
            return;
        }

        for (const line of order.lines) {
            console.log("Procesando línea de pedido:", line);

            const product = line.get_product ? line.get_product() : line.product;
            if (!product || typeof product !== 'object') {
                console.error("Producto no válido para la línea:", line);
                continue;
            }

            var taxes_ids = line.tax_ids || product.taxes_id || [];
            var valor_impuesto = "0";


            var productName = product.default_code
                ? product.default_code.replace("&", "") + " " + product.display_name.replace("&", "")
                : product.display_name.replace("&", "");

            var precio_total_con_imp = line.get_price_with_tax ? line.get_price_with_tax() : line.price;
            //var precio_unit = line.get_lst_price ? line.get_lst_price() : line.price; // OJO
            var precio_unit = line.get_unit_price();
            var cantidad = line.get_quantity ? line.get_quantity() : line.quantity;
            var precio_unit_con_imp = 0;
            var porcentage_tax = 0;

            precio_unit_con_imp = precio_total_con_imp/cantidad

            porcentage_tax = ((precio_unit_con_imp/precio_unit)-1)*100

            porcentage_tax = Math.round(porcentage_tax);

            console.log(porcentage_tax);

            if (porcentage_tax == 16){
                valor_impuesto=1;
            }

            if (porcentage_tax == 8){
                valor_impuesto=2;
            }

            if (porcentage_tax == 31){
                valor_impuesto=3;
            }

            if (porcentage_tax == 0){
                valor_impuesto=0;
            }



            if (line.discount > 0) {
                var descuento = (line.discount / 100) * precio;
                precio = precio - descuento;
            }

            lineas.push({
                product: productName.slice(0, 57),
                cantidad: cantidad,
                precio: precio_unit,
                impuesto: valor_impuesto,
                descuento: 0,
            });
        }

        console.log("Líneas procesadas:", lineas);

        const paymentLines = this.currentOrder.payment_ids; // Obtener las líneas de pago de la orden actual


        if (Array.isArray(paymentLines)) {
            for (const line of paymentLines) {
                const payment_order_linesb = {
                    name: line.payment_method_id.name,
                    payment_method: line.payment_method_id.name, // ID del método de pago
                    calculate_wh_itf:line.payment_method_id.is_currency_payment, // johan
                    amount: line.amount, 
                };
                payment_order_lines.push(payment_order_linesb);
            }
        }

        var enviar_lineas = JSON.stringify(lineas);
        var line_payments = JSON.stringify(payment_order_lines);

        if (client) {
            const clientName = client.name.replace('&', '');
            const clientPhone = client.phone || '';
            const clientAddress = client.address || '';
            const clientVat = client.vat || '';

            window.open(
                "http://localhost:8080/impresora_fiscal/cargar.php?cid=" + order.pos_reference +
                "&numero_recibo=" + order.pos_reference +
                "&cliente=" + clientName +
                "&telefono=" + clientPhone +
                "&direccion=" + clientAddress +
                "&rif_cedula=" + clientVat +
                "&lineas=" + enviar_lineas +
                "&payment_order_lines=" + line_payments +
                "&order_id=" + 666,
                "width=300,height=500,scrollbars=YES"
            );
        } else {
            console.error("Datos del cliente no disponibles.");
        }
    },

    get_paymentline_by_uuid(uuid) {
        var lines = this.currentOrder.payment_ids;
        return lines.find(function (line) {
            return line.uuid === uuid;
        });
    }
});
