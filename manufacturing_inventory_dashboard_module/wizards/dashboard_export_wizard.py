
# -*- coding: utf-8 -*-

from odoo import fields, models, api, _
import base64
import csv
import io

class DashboardExportWizard(models.TransientModel):
    _name = 'dashboard.export.wizard'
    _description = 'Dashboard Data Export Wizard'

    file_name = fields.Char(string='File Name', default='dashboard_data.csv')
    file_data = fields.Binary(string='File', readonly=True)

    def action_download_file(self):
        # Generate some dummy data for CSV export
        # In a real scenario, this data would come from Odoo models
        data_to_export = [
            ['Product Name', 'Quantity', 'Price'],
            ['Widget A', 100, 15.50],
            ['Gadget B', 50, 29.99],
            ['Thingamajig C', 200, 5.00],
        ]

        # Create an in-memory text buffer to write CSV data
        output = io.StringIO()
        writer = csv.writer(output) # Default delimiter is comma
        
        # Write header
        writer.writerow(data_to_export[0])
        # Write data rows
        for row in data_to_export[1:]:
            writer.writerow(row)
        
        # Get the CSV content as a string
        csv_string = output.getvalue()
        
        # Encode the CSV string to base64
        self.file_data = base64.b64encode(csv_string.encode('utf-8'))
        
        # Ensure the filename is set (it has a default, but good to be explicit if it could change)
        self.file_name = 'dashboard_export.csv' # Changed default name for clarity of modification
        
        return {
            'type': 'ir.actions.act_url',
            'url': f'/web/content/{self._name}/{self.id}/file_data/{self.file_name}?download=true',
            'target': 'self',
        }
