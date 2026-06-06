{
    'name': 'Manufacturing and Inventory Dashboard',
    'version': '1.0',
    'category': 'Manufacturing/MRP',
    'summary': 'Interactive Dashboard for Manufacturing and Inventory KPIs',
    'description': """
<section class="oe_container">
    <div class="oe_row oe_spaced">
        <div class="oe_span12">
            <h2 class="oe_slogan">Manufacturing and Inventory Dashboard</h2>
            <p class="oe_mt32">A comprehensive Odoo dashboard module designed to provide real-time insights into manufacturing operations and inventory levels.</p>
        </div>
    </div>
</section>

<section class="oe_container">
    <div class="oe_row oe_spaced">
        <div class="oe_span12">
            <h3 class="oe_slogan">Key Features</h3>
        </div>
    </div>
    <div class="oe_row oe_spaced">
        <div class="oe_span6">
            <div class="oe_demo oe_picture oe_screenshot">
                <h4>Real-Time KPIs</h4>
                <p>Displays Key Performance Indicators (KPIs) for manufacturing orders and stock levels.</p>
            </div>
        </div>
        <div class="oe_span6">
            <div class="oe_demo oe_picture oe_screenshot">
                <h4>Interactive Charts</h4>
                <p>Interactive charts for visualizing data trends and patterns.</p>
            </div>
        </div>
    </div>
    <div class="oe_row oe_spaced">
        <div class="oe_span6">
            <div class="oe_demo oe_picture oe_screenshot">
                <h4>Date Range Filtering</h4>
                <p>Filter data by Today, This Week, This Month, This Year, or Custom ranges.</p>
            </div>
        </div>
        <div class="oe_span6">
            <div class="oe_demo oe_picture oe_screenshot">
                <h4>Drill-Down Functionality</h4>
                <p>Click on KPI cards to navigate directly to relevant Odoo records.</p>
            </div>
        </div>
    </div>
    <div class="oe_row oe_spaced">
        <div class="oe_span6">
            <div class="oe_demo oe_picture oe_screenshot">
                <h4>Dark Mode Toggle</h4>
                <p>Switch between dark and light mode for improved user experience.</p>
            </div>
        </div>
        <div class="oe_span6">
            <div class="oe_demo oe_picture oe_screenshot">
                <h4>CSV Export</h4>
                <p>Export charts and tables to CSV for further analysis.</p>
            </div>
        </div>
    </div>
    <div class="oe_row oe_spaced">
        <div class="oe_span6">
            <div class="oe_demo oe_picture oe_screenshot">
                <h4>User Customization</h4>
                <p>Per-user customization for dashboard layout and preferences.</p>
            </div>
        </div>
        <div class="oe_span6">
            <div class="oe_demo oe_picture oe_screenshot">
                <h4>Live Data Tables</h4>
                <p>Real-time tables for recent manufacturing orders and stock transfers.</p>
            </div>
        </div>
    </div>
</section>

<section class="oe_container">
    <div class="oe_row oe_spaced">
        <div class="oe_span12">
            <h3 class="oe_slogan">Dashboard Components</h3>
        </div>
    </div>
    <div class="oe_row oe_spaced">
        <div class="oe_span12">
            <ul class="oe_list">
                <li><strong>KPI Cards:</strong> Total Manufacturing Orders, Orders in Progress, Completed Orders, Total Products, Stock Value, Low Stock Items</li>
                <li><strong>Charts:</strong> Production Trends, Order Status Distribution, Stock Movements, Production Efficiency</li>
                <li><strong>Data Tables:</strong> Recent Manufacturing Orders, Recent Stock Transfers</li>
            </ul>
        </div>
    </div>
</section>

<section class="oe_container">
    <div class="oe_row oe_spaced">
        <div class="oe_span12">
            <h3 class="oe_slogan">Benefits</h3>
            <ul class="oe_list">
                <li>Improve decision-making with real-time data visualization</li>
                <li>Track manufacturing performance and inventory metrics at a glance</li>
                <li>Identify trends and patterns in production and stock movements</li>
                <li>Export data for further analysis and reporting</li>
                <li>User-friendly interface with customizable views</li>
            </ul>
        </div>
    </div>
</section>

<section class="oe_container">
    <div class="oe_row oe_spaced">
        <div class="oe_span12">
            <h3 class="oe_slogan">Technical Details</h3>
            <p><strong>Author:</strong> Muhammad Naeem</p>
            <p><strong>Price:</strong> $100.00</p>
            <p><strong>Version:</strong> 1.0</p>
            <p><strong>License:</strong> LGPL-3</p>
            <p><strong>Dependencies:</strong> mail, mrp, stock, base, web</p>
        </div>
    </div>
</section>
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