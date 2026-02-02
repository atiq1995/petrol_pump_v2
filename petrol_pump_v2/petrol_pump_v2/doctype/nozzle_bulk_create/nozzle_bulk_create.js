frappe.ui.form.on('Nozzle Bulk Create', {
    refresh: function(frm) {
        // Enable inline editing in the grid for key fields
        if (frm.fields_dict['nozzles_to_create'] && frm.fields_dict['nozzles_to_create'].grid) {
            const grid = frm.fields_dict['nozzles_to_create'].grid;
            // Allow editing directly in cells
            grid.editable_fields = [
                {fieldname: 'nozzle_name', columns: 3},
                {fieldname: 'fuel_tank', columns: 4},
                {fieldname: 'opening_reading', columns: 2},
                {fieldname: 'is_active', columns: 1},
            ];
            // Disable opening the row form by clicking the row; only via Edit icon
            const original_open = grid.open_grid_row;
            grid.open_grid_row = function(row) {
                if (row && row.open_from_button) {
                    return original_open.call(this, row);
                }
            };
        }
    },
    petrol_pump: function(frm) {
        // Clear child rows fuel_tank when pump changes to avoid mismatch
        (frm.doc.nozzles_to_create || []).forEach(r => {
            r.fuel_tank = null;
            r.fuel_type = null;
        });
        frm.refresh_field('nozzles_to_create');
    }
});

frappe.ui.form.on('Nozzle To Create', {
    fuel_tank: function(frm, cdt, cdn) {
        const row = frappe.get_doc(cdt, cdn);
        if (row.fuel_tank) {
            frappe.db.get_value('Fuel Tank', row.fuel_tank, ['fuel_type','petrol_pump']).then(r => {
                if (r && r.message) {
                    frappe.model.set_value(cdt, cdn, 'fuel_type', r.message.fuel_type || null);
                    // If tank belongs to different pump, warn and clear
                    if (frm.doc.petrol_pump && r.message.petrol_pump && frm.doc.petrol_pump !== r.message.petrol_pump) {
                        frappe.msgprint({
                            message: `Fuel Tank belongs to ${r.message.petrol_pump}, different from selected ${frm.doc.petrol_pump}`,
                            indicator: 'orange'
                        });
                        frappe.model.set_value(cdt, cdn, 'fuel_tank', null);
                        frappe.model.set_value(cdt, cdn, 'fuel_type', null);
                    }
                }
            });
        } else {
            frappe.model.set_value(cdt, cdn, 'fuel_type', null);
        }
    },
    nozzles_to_create_add: function(frm) {
        // Ensure query filter applies to new row link field
        frm.fields_dict['nozzles_to_create'].grid.get_field('fuel_tank').get_query = function(doc) {
            if (!frm.doc.petrol_pump) return {};
            return { filters: { petrol_pump: frm.doc.petrol_pump } };
        };
    }
});

