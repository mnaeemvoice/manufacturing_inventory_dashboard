/** @odoo-module **/

import { registry } from "@web/core/registry";
import { Layout } from "@web/search/layout";
import { useService } from "@web/core/utils/hooks";
import { KeepLast } from "@web/core/utils/concurrency";
import { onWillStart, useRef, onMounted, useState } from "@odoo/owl";
import { loadBundle } from "@web/core/assets";
import { KpiCard } from "./dashboard_kpi_card";
import { DashboardChart } from "./dashboard_chart";
import { DarkModeToggle } from "./dashboard_theme";

const { Component } = owl;
console.log("✅ manufacturing dashboard JS loaded");

export class ManufacturingInventoryDashboard extends Component {
    setup() {
        // Services
        this.orm = useService("orm");
        this.action = useService("action");
        this.notification = useService("notification");

        // ✅ Initialize dashboard state first
        this.dashboard = useState({
            kpis: {},
            charts: {},
            recent_mrp_orders: [],
            recent_stock_transfers: [],
            date_range: 'this_month',
            date_start: null,
            date_end: null,
            active_kpi_filter: null, // New state variable to hold the active KPI filter domain
            active_kpi_model: null, // New state variable to hold the model of the active KPI filter
        });

        // Concurrency helper
        this.keepLast = new KeepLast();

        // Store chart component references
        this.chartRefs = {};

        // Date range options
        this.dateRangeOptions = [
            { value: 'today', label: 'Today' },
            { value: 'this_week', label: 'This Week' },
            { value: 'this_month', label: 'This Month' },
            { value: 'this_year', label: 'This Year' },
            { value: 'last_7_days', label: 'Last 7 Days' },
            { value: 'last_30_days', label: 'Last 30 Days' },
            { value: 'custom', label: 'Custom Range' },
        ];

        // Lifecycle: before component mounts
        onWillStart(async () => {
            await loadBundle("web.chartjs_lib");

            try {
                // Load saved state before fetching data
                this._loadDateRangeState();
                // Fetch data first
                await this._fetchDashboardData();

                // Ensure every chart has a name to avoid template errors
                Object.values(this.dashboard.charts || {}).forEach(chart => {
                    chart.name = chart.name || 'Untitled Chart';
                });

                // Apply dark mode preference (SAFE)
                if (this._applyDarkModePreference) {
                    this._applyDarkModePreference();
                }

            } catch (e) {
                console.error("Failed to initialize dashboard:", e);
                this.notification.add(`Failed to load dashboard: ${e.message}`, { type: "danger" });
            }
        });

        // Lifecycle: after component mounts
        onMounted(() => {
            // Mounted logic if needed
            // Dark mode already applied in onWillStart
        });
        this._fetchDashboardData = this._fetchDashboardData.bind(this);
this.onRefreshDashboard = this.onRefreshDashboard.bind(this);
this.onChangeDateRange = this.onChangeDateRange.bind(this);
this.onChangeDateStart = this.onChangeDateStart.bind(this);
this.onChangeDateEnd = this.onChangeDateEnd.bind(this);
this.onKpiCardClick = this.onKpiCardClick.bind(this);
this.onClearKpiFilter = this.onClearKpiFilter.bind(this);
    }

    // ✅ ADDED FUNCTION (without removing anything)
    _applyDarkModePreference() {
        const isDark = document.body.classList.contains("o_dark_mode");
        if (isDark) {
            document.body.classList.add("dark-dashboard");
        } else {
            document.body.classList.remove("dark-dashboard");
        }
    }

    get KpiCard() {
        return KpiCard;
    }

    get DashboardChart() {
        return DashboardChart;
    }

    get DarkModeToggle() {
        return DarkModeToggle;
    }

    async _fetchDashboardData() {
        const data = await this.keepLast.add(
            this.orm.call(
                'manufacturing.inventory.dashboard',
                'get_dashboard_data',
                [
                    this.dashboard.date_range,
                    this.dashboard.date_start,
                    this.dashboard.date_end,
                    this.dashboard.active_kpi_filter, // Pass the active filter domain
                    this.dashboard.active_kpi_model // Pass the active KPI model
                ]
            )
        );
        
        this.dashboard.kpis = data.kpis || {};
        this.dashboard.charts = data.charts || {};
        this.dashboard.recent_mrp_orders = data.recent_mrp_orders || [];
        this.dashboard.recent_stock_transfers = data.recent_stock_transfers || [];
        this.dashboard.date_range = data.date_range || 'this_month';
        this.dashboard.date_start = data.date_start || null;
        this.dashboard.date_end = data.date_end || null;

        // Inject placeholder data if sections are empty
        if (Object.keys(this.dashboard.kpis).length === 0) {
            this.dashboard.kpis.no_data_kpi = {
                technical_name: 'no_data_kpi',
                name: 'No KPIs Available',
                value: 0,
                change: 0,
                icon: 'fa fa-info-circle',
                color: 'bg-info'
            };
        }


        if (this.dashboard.recent_mrp_orders.length === 0) {
            this.dashboard.recent_mrp_orders.push({
                id: 0,
                name: 'No Recent Manufacturing Orders',
                product: 'N/A',
                quantity: 0,
                state: 'N/A',
                state_raw: 'none',
                date_planned_start: 'N/A',
                route_id: 'N/A',
                action_id: null
            });
        }

        if (this.dashboard.recent_stock_transfers.length === 0) {
            this.dashboard.recent_stock_transfers.push({
                id: 0,
                name: 'No Recent Stock Transfers',
                partner: 'N/A',
                type: 'N/A',
                state: 'N/A',
                state_raw: 'none',
                scheduled_date: 'N/A',
                action_id: null
            });
        }
    }

    async onChangeDateRange(ev) {
        this.dashboard.date_range = ev.target.value;
        if (this.dashboard.date_range !== 'custom') {
            this.dashboard.date_start = null;
            this.dashboard.date_end = null;
        }
        await this._fetchDashboardData();
    }

    async onChangeDateStart(ev) {
        this.dashboard.date_start = ev.target.value;
        await this._fetchDashboardData();
    }

    async onChangeDateEnd(ev) {
        this.dashboard.date_end = ev.target.value;
        await this._fetchDashboardData();
    }

    async onRefreshDashboard() {
        await this._fetchDashboardData();
        this.notification.add("Dashboard refreshed!", { type: "success" });
    }

  onKpiCardClick(kpi) {
    const realKpi = { ...kpi };
    console.log("KPI clicked:", realKpi);

    // Save current date range state before triggering action
    this._saveDateRangeState();

    let domain = [];
    if (realKpi.domain && Array.isArray(realKpi.domain)) {
        domain = realKpi.domain;
    } else if (realKpi.domain_json) {
        try {
            domain = JSON.parse(realKpi.domain_json);
        } catch (e) {
            this.notification.add(`Invalid domain for ${realKpi.name}`, { type: "danger" });
            return;
        }
    }

    if (!realKpi.model_id || !realKpi.model_id.model) {
        this.notification.add(`No model configured for ${realKpi.name}`, { type: "warning" });
        return;
    }

    // Add date range filters to the domain if available
    if (this.dashboard.date_start && this.dashboard.date_end) {
        let dateField;
        if (realKpi.model_id.model === 'mrp.production') {
            dateField = 'date_start'; // Using 'date_start' for mrp.production
        } else if (realKpi.model_id.model === 'stock.picking') {
            dateField = 'scheduled_date'; // Using 'scheduled_date' for stock.picking
        } else if (realKpi.model_id.model === 'stock.quant') {
            dateField = 'in_date'; // Using 'in_date' for stock.quant (as seen in _get_stock_valuation)
        } else {
            dateField = 'create_date'; // Default date field
        }
        
        // Append date filters to the existing domain
        domain.push([dateField, '>=', this.dashboard.date_start]);
        domain.push([dateField, '<=', this.dashboard.date_end]);
    }

    this.action.doAction({
        type: "ir.actions.act_window",
        name: realKpi.name,
        res_model: realKpi.model_id.model,
        view_mode: "list,form",
        views: [[false, "list"], [false, "form"]],
        domain: domain, // Now includes KPI-specific and date filters
        target: "current",
    });
}
    onClearKpiFilter() {
        this.dashboard.active_kpi_filter = null;
        this.dashboard.active_kpi_model = null;
        this._clearDateRangeState(); // Clear stored date range when clearing KPI filter
        this._fetchDashboardData();
        this.notification.add("KPI filter cleared.", { type: "info" });
    }
    exportKpiToCsv(kpi) {
    const rows = [
        ["Name", "Value", "Change"],
        [kpi.name || "", kpi.value || 0, kpi.change || 0],
    ];

    const csvContent = rows.map(r => r.join(",")).join("\n");

    const blob = new Blob([csvContent], { type: "text/csv;charset=utf-8;" });
    const link = document.createElement("a");
    link.href = URL.createObjectURL(blob);
    link.download = (kpi.technical_name || "kpi") + ".csv";
    link.click();
}
exportChartToCsv(chart)
{
    if (!chart?.data || !chart.data.labels) {
    this.notification.add("No chart data to export", { type: "warning" });
    return;
}
    const rows = [["Label", ...chart.data.datasets.map(d => d.label)]];

    chart.data.labels.forEach((label, i) => {
        const row = [label];
        chart.data.datasets.forEach(ds => row.push(ds.data[i] || 0));
        rows.push(row);
    });

    const csvContent = rows.map(r => r.join(",")).join("\n");

    const blob = new Blob([csvContent], { type: "text/csv;charset=utf-8;" });
    const link = document.createElement("a");
    link.href = URL.createObjectURL(blob);
    link.download = (chart.technical_name || "chart") + ".csv";
    link.click();
}


onConfigDashboard() {
    this.notification.add("Configure dashboard clicked", { type: "info" });
}

onTableRowClick(model, resId, actionId) {
    if (actionId) {
        this.action.doAction(actionId);
    } else {
        this.action.doAction({
            type: "ir.actions.act_window",
            res_model: model,
               view_mode: "list,form",
            res_id: resId,
            views: [[false, "form"]],
        });
    }
}

    // Utility functions for session storage
    _saveDateRangeState() {
        sessionStorage.setItem('dashboard_date_range', this.dashboard.date_range);
        sessionStorage.setItem('dashboard_date_start', this.dashboard.date_start);
        sessionStorage.setItem('dashboard_date_end', this.dashboard.date_end);
    }

    _loadDateRangeState() {
        const storedDateRange = sessionStorage.getItem('dashboard_date_range');
        const storedDateStart = sessionStorage.getItem('dashboard_date_start');
        const storedDateEnd = sessionStorage.getItem('dashboard_date_end');

        if (storedDateRange && storedDateRange !== 'custom') {
            this.dashboard.date_range = storedDateRange;
            this.dashboard.date_start = storedDateStart === 'null' ? null : storedDateStart;
            this.dashboard.date_end = storedDateEnd === 'null' ? null : storedDateEnd;
        } else if (storedDateRange === 'custom' && storedDateStart && storedDateEnd) {
             this.dashboard.date_range = storedDateRange;
             this.dashboard.date_start = storedDateStart;
             this.dashboard.date_end = storedDateEnd;
        }
    }

    _clearDateRangeState() {
        sessionStorage.removeItem('dashboard_date_range');
        sessionStorage.removeItem('dashboard_date_start');
        sessionStorage.removeItem('dashboard_date_end');
    }

}

ManufacturingInventoryDashboard.template = "manufacturing_inventory_dashboard.Dashboard";
ManufacturingInventoryDashboard.components = { Layout, KpiCard, DashboardChart, DarkModeToggle };

registry.category("actions").add(
    "manufacturing_inventory_dashboard.dashboard_action",
    ManufacturingInventoryDashboard
);
registry.category("actions").add("manufacturing_inventory_dashboard.dashboard_action", ManufacturingInventoryDashboard, { force: true });
