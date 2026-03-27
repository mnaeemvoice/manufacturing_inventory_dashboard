/** @odoo-module **/
import { Component } from "@odoo/owl";

export class KpiCard extends Component {
    static template = "manufacturing_inventory_dashboard.kpi_card_template";

    // KPI click
    onClick(ev) {
        ev.preventDefault();
        console.log("KpiCard clicked:", this.props.kpi);
        if (this.props.onClick && this.props.kpi) {
            this.props.onClick(this.props.kpi);
        }
    }

    // Export click
    onExportClick(ev) {
        ev.stopPropagation();
        if (this.props.onExport && this.props.kpi) {
            this.props.onExport(this.props.kpi);
        }
    }

    // KPI change class
    get kpiChangeClass() {
        const change = this.props.kpi?.change;
        if (change > 0) return "kpi-positive";
        if (change < 0) return "kpi-negative";
        return "kpi-neutral";
    }

    // KPI change icon
    get kpiChangeIcon() {
        const change = this.props.kpi?.change;
        if (change > 0) return "fa fa-arrow-up";
        if (change < 0) return "fa fa-arrow-down";
        return "fa fa-minus";
    }
}