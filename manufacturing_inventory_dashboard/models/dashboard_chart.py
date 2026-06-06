import json

from datetime import datetime, date, timedelta
from odoo import models, fields, api, _
import logging

_logger = logging.getLogger(__name__)


class DashboardChart(models.Model):
    _name = 'dashboard.chart'
    _description = 'Dashboard Chart Configuration'
    domain_json_id = fields.Many2one('ir.model.fields', string='Domain JSON Field',
                                     help="Select a field to filter domain if needed")
    name = fields.Char(string='Chart Name', required=True)
    technical_name = fields.Char(string='Technical Name', required=True,
                                 help="Unique identifier for the chart (e.g., mo_status_pie)")
    chart_type = fields.Selection([
        ('bar', 'Bar Chart'),
        ('line', 'Line Chart'),
        ('pie', 'Pie Chart'),
        ('doughnut', 'Doughnut Chart'),
    ], string='Chart Type', required=True, default='bar')
    model_id = fields.Many2one(
        'ir.model',
        string='Related Model',
        required=True,
        ondelete='cascade'
    )
    domain_json = fields.Text(string='Domain (JSON)', default='[]',
                              help="JSON-encoded Odoo domain to filter records for the chart.")
    group_by_field = fields.Char(string='Group By Field', help="Field name to group data by (e.g., state, product_id)")
    aggregate_method = fields.Selection([
        ('count', 'Count Records'),
        ('sum_field', 'Sum of a Field'),
        ('avg_field', 'Average of a Field'),
    ], string='Aggregation Method', default='count')
    field_to_aggregate = fields.Char(string='Field to Aggregate',
                                     help="Name of the field to sum/average (if applicable)")
    custom_chart_method = fields.Char(string='Custom Chart Method',
                                      help="Name of a Python method in this model for custom data generation.")
    chart_options = fields.Text(string='Chart.js Options (JSON)',
                                help="JSON-encoded Chart.js options for advanced customization.")

    _sql_constraints = [
        ('technical_name_uniq', 'unique(technical_name)', 'The technical name of the chart must be unique!'),
    ]

    @api.model
    def _get_chart_data(self, date_start, date_end, active_kpi_filter=None, active_kpi_model=None):
        self.ensure_one()

        # If custom method is defined, call it
        if self.custom_chart_method:
            if hasattr(self, self.custom_chart_method) and callable(getattr(self, self.custom_chart_method)):
                try:
                    _logger.debug("Calling custom chart method: %s for chart %s", self.custom_chart_method, self.name)
                    return getattr(self, self.custom_chart_method)(date_start, date_end)
                except Exception as e:
                    _logger.error("Error in custom chart method %s for chart %s: %s", self.custom_chart_method,
                                  self.name, e)
                    return {'error': _("Error in custom chart method: %s") % str(e)}
            else:
                _logger.warning("Custom chart method '%s' not found or not callable for chart %s",
                                self.custom_chart_method, self.name)
                return {'error': _("Custom chart method '%s' not found or not callable") % self.custom_chart_method}

        model = self.env[self.model_id.model]

        # Safe JSON load for domain
        try:
            domain = json.loads(self.domain_json) if self.domain_json else []
        except (json.JSONDecodeError, TypeError):
            domain = []

        # Add date filtering
        date_field = 'create_date'
        if self.model_id.model == 'mrp.production':
            date_field = 'date_start'
        elif self.model_id.model == 'stock.picking':
            date_field = 'scheduled_date'

        if date_start and date_end:
            domain.extend([
                (date_field, '>=', date_start),
                (date_field, '<=', date_end),
            ])

        _logger.debug("Final domain for chart %s: %s", self.name, domain)

        if not self.group_by_field:
            _logger.error('Group By Field is required for standard charts in chart %s.', self.name)
            return {'error': _('Group By Field is required for standard charts.')}

        # Prepare read_group fields
        read_group_fields = [self.group_by_field]
        if self.aggregate_method == 'count':
            read_group_fields.append('__count')
        elif self.aggregate_method in ['sum_field', 'avg_field'] and self.field_to_aggregate:
            aggregate_func = 'sum' if self.aggregate_method == 'sum_field' else 'avg'
            read_group_fields.append(f'{self.field_to_aggregate}:{aggregate_func}')

        _logger.debug("Read group fields for chart %s: %s", self.name, read_group_fields)

        # Perform aggregation
        raw_data = model.read_group(domain, read_group_fields, [self.group_by_field], lazy=False)
        _logger.debug("Raw data from read_group for chart %s: %s", self.name, raw_data)

        labels = []
        data = []

        if not raw_data:
            _logger.debug("No records found for chart %s with domain %s", self.name, domain)

        for item in raw_data:
            group_by_value = item.get(self.group_by_field)

            # Label handling
            if isinstance(group_by_value, tuple):
                labels.append(group_by_value[1])
            elif group_by_value is False:
                labels.append(_('Undefined'))
            else:
                if self.group_by_field in model._fields and model._fields[self.group_by_field].type == 'selection':
                    labels.append(
                        dict(model._fields[self.group_by_field].selection).get(group_by_value, group_by_value)
                    )
                else:
                    labels.append(group_by_value)

            # Data handling
            if self.aggregate_method == 'count':
                data.append(item.get('__count', 0))
            elif self.aggregate_method == 'sum_field':
                data.append(item.get(f'{self.field_to_aggregate}_sum', 0))
            elif self.aggregate_method == 'avg_field':
                data.append(item.get(f'{self.field_to_aggregate}_avg', 0))

        _logger.debug("Final labels for chart %s: %s", self.name, labels)
        _logger.debug("Final data for chart %s: %s", self.name, data)

        return {
            'name': self.name,
            'type': self.chart_type or 'bar',
            'data': {
                'labels': labels,
                'datasets': [
                    {
                        'label': self.name,
                        'data': data
                    }
                ]
            },
            'options': json.loads(self.chart_options) if self.chart_options else {}
        }
    # Custom Chart Data Generation Methods (examples)
    def _get_mo_status_pie_data(self, date_start, date_end):
        # Example: Manufacturing orders by status
        domain = [('create_date', '>=', date_start), ('create_date', '<=', date_end)] if date_start and date_end else []
        read_group_res = self.env['mrp.production'].read_group(domain, ['state'], ['state'], lazy=False)

        labels = []
        data = []
        for res in read_group_res:
            labels.append(dict(self.env['mrp.production']._fields['state'].selection).get(res['state'], res['state']))
            data.append(res.get('__count', 0))

        return {
            'labels': labels,
            'datasets': [{'label': _('Manufacturing Orders by Status'), 'data': data}]
        }

    def _get_product_wise_stock_line_data(self, date_start, date_end):
        # Example: Product-wise stock movements over time
        search_domain = [
            ('state', '=', 'done'),
            ('date', '>=', date_start),
            ('date', '<=', date_end)
        ] if date_start and date_end else [('state', '=', 'done')]
        moves = self.env['stock.move'].search(search_domain, order='date')

        data_by_product = {}
        dates_set = set()
        for move in moves:
            product_name = move.product_id.display_name
            move_date = fields.Date.to_string(move.date)
            dates_set.add(move_date)
            if product_name not in data_by_product:
                data_by_product[product_name] = {}
            data_by_product[product_name][move_date] = data_by_product[product_name].get(move_date,
                                                                                         0) + move.product_qty

        all_dates = sorted(list(dates_set))
        datasets = []
        for product_name, daily_data in data_by_product.items():
            dataset_data = [daily_data.get(d, 0) for d in all_dates]
            datasets.append({'label': product_name, 'data': dataset_data, 'fill': False})

        return {
            'labels': all_dates,
            'datasets': datasets
        }

    def _get_stock_picking_type_doughnut_data(self, date_start, date_end):
        # Example: Stock transfers by type (incoming, outgoing, internal)
        domain = [('scheduled_date', '>=', date_start),
                  ('scheduled_date', '<=', date_end)] if date_start and date_end else []
        read_group_res = self.env['stock.picking'].read_group(domain, ['picking_type_id'], ['picking_type_id'],
                                                              lazy=False)

        labels = []
        data = []
        for res in read_group_res:
            if res['picking_type_id']:
                labels.append(res['picking_type_id'][1])
            else:
                labels.append(_('Undefined Type'))
            data.append(res.get('__count', 0))

        return {
            'labels': labels,
            'datasets': [{'label': _('Stock Transfers by Type'), 'data': data}]
        }