/** @odoo-module **/

import { Component, onMounted, onWillUnmount, useRef, useEffect } from "@odoo/owl";

export class DashboardChart extends Component {
    static template = "manufacturing_inventory_dashboard.chart_template";

    setup() {
        this.chartRef = useRef("chartCanvas");
        this.chartInstance = null;

        // ✅ Sirf tab re-render jab chartData change ho
        useEffect(
            () => {
                this.renderChart();
                return () => {
                    if (this.chartInstance) {
                        this.chartInstance.destroy();
                        this.chartInstance = null;
                    }
                };
            },
            () => [this.props.chartData]
        );
    }

    onMounted() {
        this.renderChart();
    }

    onWillUnmount() {
        if (this.chartInstance) {
            this.chartInstance.destroy();
            this.chartInstance = null;
        }
    }

    renderChart() {
        if (!this.chartRef.el || !this.props.chartData) {
            return;
        }

        const ctx = this.chartRef.el.getContext("2d");

        const chartData = this.props.chartData;

        if (!chartData.data) {
            return;
        }

        // destroy old chart safely
        if (this.chartInstance) {
            this.chartInstance.destroy();
        }

        this.chartInstance = new window.Chart(ctx, {
            type: chartData.type || "bar",
            data: chartData.data,
            options: chartData.options || {},
        });
    }

    onExportClick(ev) {
        ev.preventDefault();
        if (this.props.onExport) {
            this.props.onExport(this.props.chartData);
        }
    }
}