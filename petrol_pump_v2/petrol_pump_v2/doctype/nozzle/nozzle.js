frappe.ui.form.on('Nozzle', {
    refresh: function(frm) {
        frm.set_query('fuel_tank', function() {
            if (!frm.doc.petrol_pump) {
                return {};
            }
            return {
                filters: {
                    petrol_pump: frm.doc.petrol_pump
                }
            };
        });
    },
    fuel_tank: function(frm) {
        if (frm.doc.fuel_tank) {
            frappe.db.get_value('Fuel Tank', frm.doc.fuel_tank, 'fuel_type').then(r => {
                if (r && r.message && r.message.fuel_type) {
                    frm.set_value('fuel_type', r.message.fuel_type);
                }
            });
        } else {
            frm.set_value('fuel_type', null);
        }
    }
});

