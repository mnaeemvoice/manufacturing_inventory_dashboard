
import odoo
from odoo import models, fields, api, _
from datetime import datetime, date, timedelta

import logging
import json
from odoo.tools.safe_eval import safe_eval
_logger = logging.getLogger(__name__)


class DashboardJsonDomain(models.Model):
    _name = 'dashboard.json.domain'
    _description = 'Dashboard JSON Domain Helper'

    name = fields.Char(string='Domain JSON', required=True, help="Canonical JSON string for a domain")
    _sql_constraints = [
        ('name_uniq', 'unique(name)', 'The domain JSON must be unique!'),
    ]



class DashboardKpi(models.Model):
        def _safe_kpi_value_retrieval(self, kpi_calculation_func, *args, **kwargs):
            try:
                value = kpi_calculation_func(*args, **kwargs)
                return value if value is not None else 0
            except Exception:
                return 0

        _name = 'dashboard.kpi'
        _description = 'Dashboard KPI'

        filter_field_id = fields.Many2one(
            'ir.model.fields',
            string="Filter Field",
            domain="[('model_id','=',model_id)]"
        )

        filter_operator = fields.Selection([
            ('=', '='),
            ('!=', '!='),
            ('>', '>'),
            ('<', '<'),
            ('>=', '>='),
            ('<=', '<='),
            ('ilike', 'Contains'),
            ('in', 'In'),
        ], string="Operator")

        filter_value = fields.Char(string="Value")
        drill_down_domain_id = fields.Many2one(
            'ir.filters',
            string='Drill-down Filter',
            domain="[('model_id', '=', model_id)]",
            help="Select a saved filter to apply when drilling down"
        )
        name = fields.Char(string='KPI Name', required=True)
        technical_name = fields.Char(string='Technical Name', required=True, help="Unique identifier for the KPI (e.g., total_mo_count)")
        model_id = fields.Many2one(
            'ir.model',
            string='Related Model',
            required=True,
            ondelete='cascade'
        )
        selection_options = fields.Many2many(
            'ir.model.data',  # dummy model just to hold options
            string="Field Options",
            compute="_onchange_filter_field_id"
        )
        date_field_map = {
            'mrp.production': 'create_date',  # Changed from 'date_start' to 'create_date'
            'stock.picking': 'scheduled_date',
            'stock.quant': 'in_date',
        }
        domain_json_id = fields.Many2one(
            'ir.filters',
            string='Saved Filter Domain',
            help="Select a saved filter (from Advanced Search) to use as domain"
        )

        calculation_method = fields.Selection([
            ('count', 'Count Records'),
            ('sum_field', 'Sum of a Field'),
            ('avg_field', 'Average of a Field'),
            ('custom', 'Custom Python Method'),
        ], string='Calculation Method', required=True, default='count')
        field_to_aggregate = fields.Char(string='Field to Aggregate', help="Name of the field to sum/average (if applicable)")
        kpi_custom_method_name = fields.Char(string='Custom Method Name', help="Name of the Python method in this model for custom calculation")
        icon = fields.Char(string='Icon Class', default='fa fa-star', help="Font Awesome icon class (e.g., fa fa-cube)")
        color = fields.Char(string='Color Class', default='bg-primary', help="Bootstrap color class (e.g., bg-primary, bg-success)")
        drill_down_action_id = fields.Many2one('ir.actions.act_window', string='Drill-down Action', help="Action to open when clicking the KPI")


        _sql_constraints = [
            ('technical_name_uniq', 'unique(technical_name)', 'The technical name of the KPI must be unique!'),
        ]

        @api.onchange('model_id')
        def _onchange_model_id(self):
            for record in self:
                record.domain_json_id = False
                record.drill_down_domain_id = False
                record.filter_field_id = False
                record.filter_operator = False
                record.filter_value = False
                record.drill_down_action_id = False

            if self.model_id:
                return {
                    'domain': {
                        'domain_json_id': [('model_id', '=', self.model_id.id)],  # ـــ ـــ ـــ ــــ ــــ change ـــ ـــــ
                        'drill_down_domain_id': [('model_id', '=', self.model_id.id)],
                        'filter_field_id': [('model_id', '=', self.model_id.id)],
                        'drill_down_action_id': [('res_model', '=', self.model_id.model)],
                    }
                }
            else:
                return {
                    'domain': {
                        'domain_json_id': [],
                        'drill_down_domain_id': [],
                        'filter_field_id': [],
                        'drill_down_action_id': [],
                    }
                }
        @api.onchange('filter_field_id')
        def _onchange_filter_field_id(self):
            """
            جب filter_field_id change ہو تو اس کے مطابق value input/dropdown تیار کریں
            """
            for record in self:
                record.filter_value = False  # reset previous value
                record.selection_options = []

                if record.filter_field_id:
                    field = record.filter_field_id

                    # Selection type
                    if field.ttype == 'selection':
                        record.selection_options = field.selection  # [('draft','Draft'), ('done','Done')...]

                    # Many2one type
                    elif field.ttype == 'many2one':
                        model = self.env[field.relation]
                        record.selection_options = [(r.id, r.display_name) for r in model.search([])]

                    # Boolean
                    elif field.ttype == 'boolean':
                        record.selection_options = [(True, 'Yes'), (False, 'No')]

                    # Other types (Char, Integer, Float, Date)
                    else:
                        record.selection_options = []  # user manually input

                else:
                    record.selection_options = []
        def _get_stock_valuation(self, date_start, date_end):
            # Ensure we have a model for stock.quant
            if not self.env['ir.model'].search([('model', '=', 'stock.quant')]):
                return 0.0

            # Build the domain for internal stock quants
            domain = [
                ('location_id.usage', '=', 'internal'), # Only consider internal stock
                ('quantity', '>', 0),                  # Only quants with positive quantity
            ]

            if date_start and date_end:
                # Use the 'in_date' or 'create_date' for quants to filter by date
                # 'in_date' is more appropriate for stock movements/receipts
                domain.extend([
                    ('in_date', '>=', date_start.strftime('%Y-%m-%d 00:00:00')),
                    ('in_date', '<=', datetime.combine(date_end, datetime.max.time())),
                ])

            # Search for stock quants matching the domain
            quants = self.env['stock.quant'].search(domain)

            total_value = 0.0
            for quant in quants:
                # Ensure product and cost exist before calculating
                if quant.product_id and quant.product_id.standard_price is not None:
                    total_value += quant.product_id.standard_price * quant.quantity
            return total_value

        def _get_mrp_completion_rate(self, records, date_start, date_end):
            total_mrp = self.env['mrp.production'].search_count([('create_date', '>=', date_start), ('create_date', '<=', date_end)]) if date_start and date_end else self.env['mrp.production'].search_count([]) # Changed 'date_start' to 'create_date'
            done_mrp = records.search_count([('state', '=', 'done')])
            return (done_mrp / total_mrp * 100) if total_mrp else 0.0

        # Add this inside the DashboardKpi class
        def _get_previous_period_dates(self, date_start, date_end):
            """
            Returns start and end dates of the previous period
            with the same length as current period.
            """
            self.ensure_one()
            if not date_start or not date_end:
                return None, None

            period_length = (date_end - date_start).days + 1
            prev_end = date_start - timedelta(days=1)
            prev_start = prev_end - timedelta(days=period_length - 1)
            return prev_start, prev_end

        @api.model
        def _get_kpi_value(self, date_start=None, date_end=None, external_filter=None, external_model=None):
            self.ensure_one()
            current_value = 0.0
            change = 0.0
            prev_date_start, prev_date_end = None, None # Initialize here

            try:
                model_name = self.model_id.model
                model = self.env[model_name]
            except Exception as e:
                _logger.error("Model %s not found for KPI %s: %s", self.model_id.model, self.name, e)
                return current_value, change

            # Base domain from saved filter
            base_domain = []
            if self.domain_json_id:
                try:
                    base_domain = safe_eval(self.domain_json_id.domain or '[]', {})
                    if not isinstance(base_domain, list):
                        base_domain = []
                except Exception as e:
                    _logger.warning("Invalid domain for KPI %s: %s", self.name, e)

            # Dynamic filter
            if self.filter_field_id and self.filter_operator and self.filter_value:
                value = self.filter_value
                field = self.filter_field_id

                # Cast value according to field type
                if field.ttype in ['integer', 'float']:
                    value = float(value)
                elif field.ttype == 'many2one':
                    value = int(value)
                elif field.ttype == 'boolean':
                    value = value in [True, 'True', '1', 'yes']

                base_domain.append((field.name, self.filter_operator, value))

            # Apply external filter if provided and matches the model
            if external_filter and external_model == model_name:
                try:
                    external_domain = safe_eval(external_filter or '[]', {})
                    if isinstance(external_domain, list) and external_domain:
                        base_domain = ['&'] + base_domain + external_domain # Corrected domain merging
                except Exception as e:
                    _logger.error("Invalid external filter: %s", e)

            # --- Debugging logs ---
            _logger.warning("MODEL: %s", model_name)
            _logger.warning("BASE DOMAIN (after static, dynamic, external): %s", base_domain)
            # ---------------------

            # Now create period-specific domains from the combined base_domain
            current_period_domain = list(base_domain)
            previous_period_domain = list(base_domain)

            # Add date range filters if provided
            if date_start and date_end:
                date_field = self.date_field_map.get(model_name)
                if date_field:
                    current_period_domain.extend([
                        (date_field, '>=', date_start.strftime('%Y-%m-%d 00:00:00')),
                        (date_field, '<=', datetime.combine(date_end, datetime.max.time())),
                    ])

                    # Get previous period dates
                    prev_date_start, prev_date_end = self._get_previous_period_dates(date_start, date_end)
                    if prev_date_start and prev_date_end:
                        previous_period_domain.extend([
                            (date_field, '>=', prev_date_start.strftime('%Y-%m-%d 00:00:00')),
                            (date_field, '<=', datetime.combine(prev_date_end, datetime.max.time())),
                        ])
                else:
                    _logger.warning("No date_field configured for model %s in KPI %s. Date filtering skipped.", model_name, self.name)

            # --- Debugging logs ---
            _logger.warning("FINAL DOMAIN (Current Period): %s", current_period_domain)
            # ---------------------

            # Fetch current records
            try:
                # Quick Debug Trick: Test without filters
                # records_unfiltered = model.search([])
                # _logger.warning("TOTAL RECORDS WITHOUT FILTER: %s", len(records_unfiltered))

                records = model.search(current_period_domain)
                _logger.warning("RECORD COUNT: %s", len(records))
            except Exception as e:
                _logger.error("Error fetching records for KPI %s with domain %s: %s", self.name, current_period_domain, e)
                records = self.env[model_name].browse([])

            # Calculate current value
            try:
                if self.calculation_method == 'count':
                    current_value = len(records)
                elif self.calculation_method == 'sum_field' and self.field_to_aggregate:
                    current_value = sum(records.mapped(self.field_to_aggregate))
                elif self.calculation_method == 'avg_field' and self.field_to_aggregate:
                    current_value = sum(records.mapped(self.field_to_aggregate)) / len(records) if records else 0.0
                elif self.calculation_method == 'custom' and self.kpi_custom_method_name:
                    if hasattr(self, self.kpi_custom_method_name):
                        current_value = getattr(self, self.kpi_custom_method_name)(records, date_start, date_end)
            except Exception as e:
                _logger.error("Error calculating current value for KPI %s: %s", self.name, e)
                current_value = 0.0

            # Previous period calculation
            try:
                # Need to determine prev_date_start and prev_date_end for custom methods if not set above
                # prev_date_start, prev_date_end are already initialized at the beginning of the function

                # Re-fetch previous period records to ensure date filters are applied correctly
                previous_records = model.search(previous_period_domain)
                previous_value = 0.0

                if self.calculation_method == 'count':
                    previous_value = len(previous_records)
                elif self.calculation_method == 'sum_field' and self.field_to_aggregate:
                    previous_value = sum(previous_records.mapped(self.field_to_aggregate))
                elif self.calculation_method == 'avg_field' and self.field_to_aggregate:
                    previous_value = sum(previous_records.mapped(self.field_to_aggregate)) / len(previous_records) if previous_records else 0.0
                elif self.calculation_method == 'custom' and self.kpi_custom_method_name:
                    if hasattr(self, self.kpi_custom_method_name):
                        # For custom methods, recalculate for previous period using its date range
                        # The _get_previous_period_dates was called earlier, so prev_date_start/end should be available if date_start/end were.
                        previous_value = getattr(self, self.kpi_custom_method_name)(previous_records, prev_date_start, prev_date_end)


                # Percentage change
                if previous_value != 0:
                    change = ((current_value - previous_value) / previous_value) * 100
                elif current_value != 0:
                    change = 100.0
                else:
                    change = 0.0
            except Exception as e:
                _logger.warning("Error calculating change for KPI %s: %s", self.name, e)
                change = 0.0

            return current_value, change