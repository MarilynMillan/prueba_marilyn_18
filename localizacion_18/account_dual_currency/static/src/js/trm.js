/** @odoo-module **/
import { registry } from "@web/core/registry";
import { useService } from "@web/core/utils/hooks";
const { Component, onWillStart, useState } = owl;
import { session } from "@web/session";

class TRM extends Component {
    setup() {
        super.setup(...arguments);
        this.state = useState({ trm: 0 });
        var company_id = session.company_id;
        this.orm = useService('orm');
        onWillStart(async () => {
            //var trm = await this.orm.call('res.currency.rate', 'get_trm_systray', [company_id]);
            var trm =0
            const rates = await this.orm.searchRead('res.currency.rate',
            [['currency_id', '=', 1]], // Filtrar por la moneda actual
            ['inverse_company_rate'], // Campos a leer
            { limit: 1, order: 'name desc' } // Ordenar por fecha y limitar a 1
            );
            if (rates.length > 0) {
                trm= rates[0].inverse_company_rate;
            }
            else{
                trm = 0
            }
            this.state.trm = trm;
        });
    }

    get trm() {
        return this.state.trm;
    }
    _onClick() {

    }
}

TRM.template = "trm_menu";
export const trmItem = { Component: TRM};

registry.category("systray").add("TRM", trmItem, {sequence: 1});
