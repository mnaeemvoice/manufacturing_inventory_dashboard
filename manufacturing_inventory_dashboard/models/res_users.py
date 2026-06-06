# -*- coding: utf-8 -*-
from odoo import models, fields, api

class ResUsers(models.Model):
    _inherit = 'res.users'

    dashboard_kpi_visibility_ids = fields.Many2many(
        'dashboard.kpi',
        'res_users_dashboard_kpi_rel',
        'user_id',
        'kpi_id',
        string='Visible KPIs on Dashboard',
        help="Select which KPIs this user prefers to see on the Manufacturing and Inventory Dashboard. If empty, all default KPIs will be shown."
    )
    dashboard_chart_visibility_ids = fields.Many2many(
        'dashboard.chart',
        'res_users_dashboard_chart_rel',
        'user_id',
        'chart_id',
        string='Visible Charts on Dashboard',
        help="Select which charts this user prefers to see on the Manufacturing and Inventory Dashboard. If empty, all default charts will be shown."
    )
    dashboard_dark_mode = fields.Boolean(string='Dark Mode Enabled', default=False)

    @api.model
    def action_open_dashboard_preferences(self):
        """Return a window action for the current user dashboard preferences."""
        return {
            'type': 'ir.actions.act_window',
            'name': 'Dashboard Preferences',
            'res_model': 'res.users',
            'res_id': self.env.uid,  # current user
            'view_mode': 'form',
            'views': [
                (self.env.ref('manufacturing_inventory_dashboard.view_users_form_dashboard_preferences').id, 'form')
            ],
            'target': 'new',
        }