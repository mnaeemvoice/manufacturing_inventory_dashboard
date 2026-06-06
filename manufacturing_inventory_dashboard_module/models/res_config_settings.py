# -*- coding: utf-8 -*-

from odoo import models, fields, api

class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'
    _name = 'res.config.settings'
    _description = "Configuration for Manufacturing Inventory Dashboard"

    # Example: A global setting for a KPI threshold
    # default_mo_completion_target = fields.Float(
    #     string="Default MO Completion Target (%)",
    #     config_parameter='manufacturing_inventory_dashboard.default_mo_completion_target',
    #     default=90.0,
    #     help="Target percentage for Manufacturing Order completion rate."
    # )

    # Example: A global setting to enable/disable certain dashboard features
    # enable_dark_mode_feature = fields.Boolean(
    #     string="Enable Dark Mode Toggle",
    #     config_parameter='manufacturing_inventory_dashboard.enable_dark_mode_feature',
    #     default=True,
    #     help="Allow users to toggle dark mode on the dashboard."
    # )

    # This model can be further extended for specific dashboard configurations if needed.
    # For instance, defining which KPIs/Charts are available globally, or default configurations.
