{
    'name': 'Manufacturing and Inventory Dashboard',
    'version': '1.0',
    'category': 'Manufacturing/MRP',
    'summary': 'Interactive Dashboard for Manufacturing and Inventory KPIs',
    'description': """
        A comprehensive Odoo dashboard module designed to provide real-time insights
        into manufacturing operations and inventory levels.

        Key Features:
        - Displays Key Performance Indicators (KPIs) for manufacturing orders and stock.
        - Interactive charts for visualizing data trends.
        - Date range filtering (Today, This Week, This Month, This Year, Custom).
        - Drill-down functionality to relevant Odoo records.
        - Dark mode toggle for improved user experience.
        - CSV export for charts and tables.
        - Per-user customization for dashboard layout.
        - Live data tables for recent manufacturing orders and stock transfers.
        
        Dashboard Overview:
        - Real-time KPI cards showing manufacturing order status, production efficiency, and inventory levels
        - Interactive charts for production trends, stock movements, and order analysis
        - Recent manufacturing orders table with quick access to order details
        - Recent stock transfers table with transfer status tracking
        - Customizable date range filters for flexible data analysis
        - Dark/Light mode theme toggle for better visibility
        
        Benefits:
        - Improve decision-making with real-time data visualization
        - Track manufacturing performance and inventory metrics at a glance
        - Identify trends and patterns in production and stock movements
        - Export data for further analysis and reporting
        - User-friendly interface with customizable views
    """,
    'author': 'Muhammad Naeem',
    'website': 'https://getodooai.com/',
    'price': '100.00',
    'depends': ['mail', 'mrp', 'stock', 'base', 'web'],
    'data': [
        # Security first
        'security/dashboard_security.xml',
        'security/ir.model.access.csv',

        # Core data & cron
        'data/dashboard_data.xml',
        'data/dashboard_json_data.xml',
        'data/ir_cron_data.xml',

        # Server action and dashboard menu
        'views/res_users_views.xml',  # contains the server action definition
        'views/dashboard_views.xml',   # contains XML for menu, form, list, charts, KPIs
        'views/res_config_settings_views.xml',

        # Wizards
        'wizards/dashboard_export_wizard_views.xml',
    ],
    'assets': {
        'web.assets_backend': [
            # Chart.js first
            'manufacturing_inventory_dashboard/static/lib/chart.min.js',

            # Styles first
            'manufacturing_inventory_dashboard/static/src/scss/dashboard.scss',

            # JS core files
            'manufacturing_inventory_dashboard/static/src/js/dashboard.js',
            'manufacturing_inventory_dashboard/static/src/js/dashboard_chart.js',
            'manufacturing_inventory_dashboard/static/src/js/dashboard_kpi_card.js',

            'manufacturing_inventory_dashboard/static/src/js/dashboard_theme.js',

            # XML templates loaded via JS
            'manufacturing_inventory_dashboard/static/src/xml/dashboard_templates.xml',
            'manufacturing_inventory_dashboard/static/src/xml/chart_template.xml',
            'manufacturing_inventory_dashboard/static/src/xml/kpi_card_template.xml',

            'manufacturing_inventory_dashboard/static/src/xml/recent_orders_template.xml',
            'manufacturing_inventory_dashboard/static/src/xml/recent_transfers_template.xml',
            'manufacturing_inventory_dashboard/static/src/xml/dark_mode_toggle.xml',
        ],
        'web.assets_qweb': [
            # Only QWeb templates
            'manufacturing_inventory_dashboard/static/src/xml/dashboard_templates.xml',
            'manufacturing_inventory_dashboard/static/src/xml/chart_template.xml',
            'manufacturing_inventory_dashboard/static/src/xml/kpi_card_template.xml',

            'manufacturing_inventory_dashboard/static/src/xml/recent_orders_template.xml',
            'manufacturing_inventory_dashboard/static/src/xml/recent_transfers_template.xml',
            'manufacturing_inventory_dashboard/static/src/xml/dark_mode_toggle.xml',
        ],
    },
    'installable': True,
    'application': True,
    'auto_install': False,
    'license': 'LGPL-3',
    'images': ['static/description/banner.png'],
    'post_init_hook': 'post_init_hook',
}