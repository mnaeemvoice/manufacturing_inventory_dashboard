/** @odoo-module **/

import { Component, useState, onMounted } from "@odoo/owl";
import { useService } from "@web/core/utils/hooks";

export class DarkModeToggle extends Component {
    setup() {
        this.orm = useService("orm");
        this.state = useState({
            isDarkMode: false,
        });

        onMounted(async () => {
            const isDarkModeEnabled = await this.orm.call(
                'manufacturing.inventory.dashboard',
                'get_dark_mode_status',
                []
            );
            this.state.isDarkMode = isDarkModeEnabled;
            this._applyTheme(this.state.isDarkMode);
        });
    }

    async toggleDarkMode() {
        this.state.isDarkMode = !this.state.isDarkMode;
        this._applyTheme(this.state.isDarkMode);
        await this.orm.call(
            'manufacturing.inventory.dashboard',
            'set_dark_mode',
            [this.state.isDarkMode]
        );
        // Trigger a dashboard refresh to re-render charts with new theme colors
        this.props.onThemeChange();
    }

    _applyTheme(isDark) {
        if (isDark) {
            document.body.classList.add('o_dark_mode');
        } else {
            document.body.classList.remove('o_dark_mode');
        }
    }
}

DarkModeToggle.template = 'manufacturing_inventory_dashboard.dark_mode_toggle';
DarkModeToggle.props = {
    onThemeChange: Function,
};
