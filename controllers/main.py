from odoo import http
from odoo.http import request
import json

class ManufacturingInventoryDashboardController(http.Controller):
    
    @http.route('/manufacturing_inventory_dashboard/data', type='json', auth='user')
    def get_dashboard_data(self, date_range=None, date_start=None, date_end=None, **kw):
        dashboard_obj = request.env['manufacturing.inventory.dashboard']
        return dashboard_obj.get_dashboard_data(date_range, date_start, date_end)

    @http.route('/manufacturing_inventory_dashboard/export_kpi_csv/<string:kpi_technical_name>', type='http', auth='user')
    def export_kpi_csv(self, kpi_technical_name, date_start, date_end, **kw):
        success, csv_data = request.env['manufacturing.inventory.dashboard'].get_kpi_csv_data(
            kpi_technical_name, date_start, date_end
        )
        if not success:
            return request.not_found(description=csv_data)
        
        headers = [
            ('Content-Type', 'text/csv'),
            ('Content-Disposition', f'attachment; filename="{kpi_technical_name}_data.csv"'),
        ]
        return request.make_response(csv_data, headers)

    @http.route('/manufacturing_inventory_dashboard/export_chart_csv/<string:chart_technical_name>', type='http', auth='user')
    def export_chart_csv(self, chart_technical_name, date_start, date_end, **kw):
        success, csv_data = request.env['manufacturing.inventory.dashboard'].get_chart_csv_data(
            chart_technical_name, date_start, date_end
        )
        if not success:
            return request.not_found(description=csv_data)
        
        headers = [
            ('Content-Type', 'text/csv'),
            ('Content-Disposition', f'attachment; filename="{chart_technical_name}_data.csv"'),
        ]
        return request.make_response(csv_data, headers)

    @http.route('/manufacturing_inventory_dashboard/set_dark_mode', type='json', auth='user')
    def set_dark_mode(self, dark_mode_enabled, **kw):
        request.env.user.sudo().write({'dashboard_dark_mode': dark_mode_enabled})
        return True

    @http.route('/manufacturing_inventory_dashboard/get_dark_mode_status', type='json', auth='user')
    def get_dark_mode_status(self, **kw):
        return request.env.user.dashboard_dark_mode
