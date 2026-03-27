import logging
from odoo import models, fields, api, _
from datetime import datetime, date, timedelta
import json
import base64
import io
import csv
import ast
from odoo.tools.safe_eval import safe_eval
_logger = logging.getLogger(__name__)


class ManufacturingInventoryDashboard(models.Model):
    _name = 'manufacturing.inventory.dashboard'
    _description = 'Manufacturing and Inventory Dashboard'

    name = fields.Char(string='Dashboard Name', default='Manufacturing & Inventory Overview')

    date_range = fields.Selection([
        ('today', 'Today'),
        ('this_week', 'This Week'),
        ('this_month', 'This Month'),
        ('this_year', 'This Year'),
        ('last_7_days', 'Last 7 Days'),
        ('last_30_days', 'Last 30 Days'),
        ('custom', 'Custom Range'),
    ], string='Date Range', default='this_month')
    date_start = fields.Date(string='Start Date')
    date_end = fields.Date(string='End Date')

    # Per-User Customization fields (added to match the final module structure)
    user_kpi_ids = fields.Many2many(
        'dashboard.kpi',
        'manufacturing_inventory_dashboard_kpi_rel',
        'dashboard_id',
        'kpi_id',
        string='Visible KPIs',
        help="Select which KPIs to display on the dashboard for this user."
    )
    user_chart_ids = fields.Many2many(
        'dashboard.chart',
        'manufacturing_inventory_dashboard_chart_rel',
        'dashboard_id',
        'chart_id',
        string='Visible Charts',
        help="Select which charts to display on the dashboard for this user."
    )

    @api.model
    def set_dark_mode(self, dark_mode_enabled):
        # Correct field name
        self.env.user.sudo().write({'dashboard_dark_mode': dark_mode_enabled})

    @api.model
    def get_dark_mode_status(self):
        return self.env.user.dashboard_dark_mode

    @api.model
    def _get_default_date_range(self):
        return 'this_month'

    @api.model
    def _get_default_date_start(self):
        return (date.today().replace(day=1) if self._get_default_date_range() == 'this_month' else False)

    @api.model
    def _get_default_date_end(self):
        return (date.today() if self._get_default_date_range() == 'this_month' else False)

    def _get_dates_from_range(self, date_range, date_start, date_end):  # NOSONAR
        today = date.today()
        if date_range == 'today':
            date_start = today
            date_end = today
        elif date_range == 'this_week':
            date_start = today - timedelta(days=today.weekday())
            date_end = today + timedelta(days=6 - today.weekday())
        elif date_range == 'this_month':
            date_start = today.replace(day=1)
            next_month = today.replace(day=28) + timedelta(days=4)
            date_end = next_month - timedelta(days=next_month.day)
        elif date_range == 'this_year':
            date_start = today.replace(month=1, day=1)
            date_end = today
        elif date_range == 'last_7_days':
            date_start = today - timedelta(days=6)
            date_end = today
        elif date_range == 'last_30_days':
            date_start = today - timedelta(days=29)
            date_end = today
        return date_start, date_end

    @api.model
    def get_dashboard_data(self, date_range=None, date_start=None, date_end=None, active_kpi_filter=None,
                           active_kpi_model=None):
        if not date_range:
            date_range = self._get_default_date_range()
        if not date_start:
            date_start = self._get_default_date_start()
        if not date_end:
            date_end = self._get_default_date_end()

        if isinstance(date_start, str):
            date_start = fields.Date.from_string(date_start)
        if isinstance(date_end, str):
            date_end = fields.Date.from_string(date_end)

        date_start, date_end = self._get_dates_from_range(date_range, date_start, date_end)

        dashboard_data = {
            'kpis': {},
            'charts': {},
            'recent_mrp_orders': [],
            'recent_stock_transfers': [],
            'date_range': date_range,
            'date_start': fields.Date.to_string(date_start) if date_start else None,
            'date_end': fields.Date.to_string(date_end) if date_end else None,
        }

        kpis = self.env['dashboard.kpi'].search([])
        for kpi in kpis:
            value, change = kpi._get_kpi_value(date_start, date_end, active_kpi_filter, active_kpi_model)

            # ✅ Safe parsing of domain_json_id
            domain_list = []
            if kpi.domain_json_id:
                domain_str = kpi.domain_json_id.domain or '[]'
                try:
                    domain_list = safe_eval(domain_str)
                    if not isinstance(domain_list, list):
                        domain_list = []
                except Exception as e:
                    _logger.warning("Error parsing domain_json_id for KPI %s: %s", kpi.technical_name, e)
                    domain_list = []

            dashboard_data['kpis'][kpi.technical_name] = {
                'name': kpi.name,
                'technical_name': kpi.technical_name,
                'value': value,
                'change': change,
                'icon': kpi.icon,
                'color': kpi.color,
                'model_id': {'model': kpi.model_id.model, 'name': kpi.model_id.name} if kpi.model_id else None,
                'drill_down_action_id': kpi.drill_down_action_id.id if kpi.drill_down_action_id else None,
                'domain': domain_list,  # ✅ safely parsed
            }
        charts = self.env['dashboard.chart'].search([])
        for chart in charts:
            chart_data_response = chart._get_chart_data(date_start, date_end, active_kpi_filter, active_kpi_model)
            if 'error' in chart_data_response:
                _logger.error("Error fetching chart data for %s: %s", chart.name, chart_data_response['error'])
                dashboard_data['charts'][chart.technical_name] = {
                    'name': chart.name,
                    'technical_name': chart.technical_name,
                    'type': chart.chart_type,
                    'error': chart_data_response['error']
                }
            else:
                dashboard_data['charts'][chart.technical_name] = {
                    'name': chart.name,
                    'technical_name': chart.technical_name,
                    'type': chart.chart_type,
                    'data': chart_data_response,
                    'options': json.loads(chart.chart_options) if chart.chart_options else {},
                }

        # Dynamic domain for MRP Productions
        domain_mrp_base = [["state", "in", ["confirmed", "progress", "Done"]]]
        final_mrp_domain = self._apply_active_filter(domain_mrp_base, active_kpi_filter, active_kpi_model,
                                                     'mrp.production')

        mrp_productions = self.env['mrp.production'].search(final_mrp_domain +
                                                            [
                                                                ('date_start', '>=', date_start),
                                                                ('date_start', '<=',
                                                                 datetime.combine(date_end, datetime.max.time())),
                                                            ], order='date_start desc', limit=5)

        for mo in mrp_productions:
            dashboard_data['recent_mrp_orders'].append({
                'id': mo.id,
                'name': mo.name,
                'product': mo.product_id.display_name,
                'quantity': mo.product_qty,
                'state': dict(mo._fields['state'].selection).get(mo.state),
                'state_raw': mo.state,
                'date_start': fields.Date.to_string(mo.date_start),
                'route_id': mo.workcenter_id.name if mo.workcenter_id else False,
                'action_id': self.env.ref('mrp.mrp_production_action').id,
            })

        # Section for recent_stock_transfers
        base_domain_for_stock_transfers = []

        # Retrieve relevant KPI records for stock.picking to get their base domains
        kpi_outgoing = self.env['dashboard.kpi'].search([('technical_name', '=', 'outgoing_transfers')], limit=1)
        kpi_incoming = self.env['dashboard.kpi'].search([('technical_name', '=', 'incoming_transfers')], limit=1)

        parsed_outgoing_domain = []
        parsed_incoming_domain = []

        if kpi_outgoing and kpi_outgoing.domain_json_id:
            try:
                domain_str = kpi_outgoing.domain_json_id.domain or '[]'
                parsed_outgoing_domain = safe_eval(domain_str)
                if not isinstance(parsed_outgoing_domain, list):
                    parsed_outgoing_domain = []
            except Exception as e:
                _logger.warning("Invalid outgoing domain: %s", e)
                parsed_outgoing_domain = []

        if kpi_incoming and kpi_incoming.domain_json_id:
            try:
                domain_str = kpi_incoming.domain_json_id.domain or '[]'
                parsed_incoming_domain = safe_eval(domain_str)
                if not isinstance(parsed_incoming_domain, list):
                    parsed_incoming_domain = []
            except Exception as e:
                _logger.warning("Invalid incoming domain: %s", e)
                parsed_incoming_domain = []

        domain_stock = []
        if parsed_outgoing_domain and parsed_incoming_domain:
            domain_stock = ['|'] + parsed_outgoing_domain + parsed_incoming_domain
        elif parsed_outgoing_domain:
            domain_stock = parsed_outgoing_domain
        elif parsed_incoming_domain:
            domain_stock = parsed_incoming_domain

        # Apply active_kpi_filter if provided and relevant, *after* the base domain
        if active_kpi_filter and active_kpi_model == 'stock.picking':
            try:
                parsed_active_kpi_filter = safe_eval(active_kpi_filter) if isinstance(active_kpi_filter, str) else active_kpi_filter

                if isinstance(parsed_active_kpi_filter, list):
                    if domain_stock:
                        domain_stock = ['&'] + domain_stock + parsed_active_kpi_filter
                    else:
                        domain_stock = parsed_active_kpi_filter

            except Exception as e:
                _logger.warning("Filter parse error: %s", e)

        # Ensure date filters are applied
        final_stock_picking_domain = list(domain_stock)
        if date_start and date_end:
            final_stock_picking_domain.extend([
                ('scheduled_date', '>=', date_start),
                ('scheduled_date', '<=', datetime.combine(date_end, datetime.max.time())),
            ])

        stock_pickings = self.env['stock.picking'].search(final_stock_picking_domain, order='scheduled_date desc',
                                                          limit=5)

        for sp in stock_pickings:
            dashboard_data['recent_stock_transfers'].append({
                'id': sp.id,
                'name': sp.name,
                'partner': sp.partner_id.display_name if sp.partner_id else _('N/A'),
                'type': sp.picking_type_id.name,
                'state': dict(sp._fields['state'].selection).get(sp.state),
                'state_raw': sp.state,
                'scheduled_date': fields.Date.to_string(sp.scheduled_date),
                'action_id': self.env.ref('stock.action_picking_tree_all').id,
            })

        return dashboard_data

    @api.model
    def export_kpi_data_to_csv(self, kpi_technical_name, date_range, date_start_str, date_end_str,
                               active_kpi_filter=None, active_kpi_model=None):
        if not self.env.user:
            return {'error': "User not logged in."}

        kpi = self.env['dashboard.kpi'].search([('technical_name', '=', kpi_technical_name)], limit=1)
        if not kpi:
            _logger.warning("KPI with technical name %s not found for export.", kpi_technical_name)
            return {'error': _("KPI not found.")}

        date_start = fields.Date.from_string(date_start_str) if date_start_str else None
        date_end = fields.Date.from_string(date_end_str) if date_end_str else None

        # Retrieve the KPI value and change from the _get_kpi_value method
        value, change = kpi._get_kpi_value(date_start, date_end, active_kpi_filter, active_kpi_model)

        # Prepare CSV data
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(['KPI Name', 'Value', 'Change (%)'])
        writer.writerow([kpi.name, value, f"{change:.2f}" if change is not None else 'N/A'])

        csv_content = output.getvalue()
        b64_csv = base64.b64encode(csv_content.encode()).decode()

        # Create a URL for file download using the ir.attachment model
        # This is a common Odoo pattern for downloadable files
        attachment = self.env['ir.attachment'].create({
            'name': f"{kpi.name.replace(' ', '_').lower()}_kpi_data.csv",
            'type': 'binary',
            'datas': b64_csv,
            'res_model': 'manufacturing.inventory.dashboard',
            'res_id': self.id,  # Link to current dashboard instance if applicable
            'mimetype': 'text/csv',
        })

        _logger.info("Exported KPI %s data to CSV.", kpi_technical_name)
        return {'file_url': f'/web/content/{attachment.id}?download=true'}

    @api.model
    def export_chart_data_to_csv(self, chart_technical_name, date_range, date_start_str, date_end_str,
                                 active_kpi_filter=None, active_kpi_model=None):
        if not self.env.user:
            return {'error': "User not logged in."}

        chart = self.env['dashboard.chart'].search([('technical_name', '=', chart_technical_name)], limit=1)
        if not chart:
            _logger.warning("Chart with technical name %s not found for export.", chart_technical_name)
            return {'error': _("Chart not found.")}

        date_start = fields.Date.from_string(date_start_str) if date_start_str else None
        date_end = fields.Date.from_string(date_end_str) if date_end_str else None

        # Retrieve the chart data from the _get_chart_data method
        chart_data_response = chart._get_chart_data(date_start, date_end, active_kpi_filter, active_kpi_model)
        if 'error' in chart_data_response:
            _logger.error("Error fetching chart data for export for %s: %s", chart.name, chart_data_response['error'])
            return {'error': _("Could not retrieve chart data for export.")}

        output = io.StringIO()
        writer = csv.writer(output)

        # Determine CSV headers and data rows based on chart type and data structure
        if chart.chart_type in ['bar', 'line']:
            # Expecting data['labels'] and data['datasets']
            if 'labels' not in chart_data_response or 'datasets' not in chart_data_response:
                _logger.warning("Invalid data structure for chart %s (bar/line type) for export.", chart.name)
                return {'error': _("Invalid chart data structure for export.")}

            headers = ['Label'] + [ds['label'] for ds in chart_data_response['datasets']]
            writer.writerow(headers)
            for i, label in enumerate(chart_data_response['labels']):
                row = [label] + [ds['data'][i] if i < len(ds['data']) else '' for ds in chart_data_response['datasets']]
                writer.writerow(row)
        elif chart.chart_type in ['pie', 'doughnut']:
            # Expecting data['labels'] and data['data'] in the first dataset
            if 'labels' not in chart_data_response or 'datasets' not in chart_data_response or not chart_data_response[
                'datasets']:
                _logger.warning("Invalid data structure for chart %s (pie/doughnut type) for export.", chart.name)
                return {'error': _("Invalid chart data structure for export.")}

            headers = ['Label', 'Value']
            writer.writerow(headers)
            dataset_data = chart_data_response['datasets'][0]['data']
            for i, label in enumerate(chart_data_response['labels']):
                row = [label, dataset_data[i] if i < len(dataset_data) else '']
                writer.writerow(row)
        else:
            _logger.warning("Unsupported chart type %s for CSV export for chart %s.", chart.chart_type, chart.name)
            return {'error': _("Unsupported chart type for export.")}

        csv_content = output.getvalue()
        b64_csv = base64.b64encode(csv_content.encode()).decode()

        attachment = self.env['ir.attachment'].create({
            'name': f"{chart.name.replace(' ', '_').lower()}_chart_data.csv",
            'type': 'binary',
            'datas': b64_csv,
            'res_model': 'manufacturing.inventory.dashboard',
            'res_id': self.id,
            'mimetype': 'text/csv',
        })

        _logger.info("Exported Chart %s data to CSV.", chart_technical_name)
        return {'file_url': f'/web/content/{attachment.id}?download=true'}

    def _apply_active_filter(self, base_domain, active_kpi_filter, active_kpi_model, current_model):
        """
        Apply active KPI filter on any model dynamically
        """
        if not base_domain:
            base_domain = []

        # If model does not match -> do not apply filter
        if active_kpi_model != current_model:
            return base_domain

        if active_kpi_filter:
            try:
                # Ensure safe_eval is available for cases where it's a string
                from odoo.tools.safe_eval import safe_eval
                parsed_filter = safe_eval(active_kpi_filter) if isinstance(active_kpi_filter, str) else active_kpi_filter

                if isinstance(parsed_filter, list):
                    return ['&'] + base_domain + parsed_filter

            except Exception as e:
                _logger.warning("Filter error on %s: %s", current_model, e)

        return base_domain