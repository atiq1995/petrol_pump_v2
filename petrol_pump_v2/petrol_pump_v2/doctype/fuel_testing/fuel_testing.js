frappe.ui.form.on('Fuel Testing', {
	refresh(frm) {
		// Filter nozzle in child table by petrol pump
		frm.fields_dict.fuel_testing_details.grid.get_field('nozzle').get_query = function () {
			return {
				filters: {
					petrol_pump: frm.doc.petrol_pump,
					is_active: 1
				}
			};
		};
	},

	petrol_pump(frm) {
		// Clear table when pump changes
		frm.clear_table('fuel_testing_details');
		frm.refresh_field('fuel_testing_details');
	}
});

frappe.ui.form.on('Fuel Testing Detail', {
	nozzle(frm, cdt, cdn) {
		const row = locals[cdt][cdn];
		if (!row.nozzle) {
			frappe.model.set_value(cdt, cdn, 'fuel_type', '');
			frappe.model.set_value(cdt, cdn, 'rate', 0);
			frappe.model.set_value(cdt, cdn, 'amount', 0);
			return;
		}

		// Fetch fuel_type from Nozzle, then get active rate from server
		frappe.db.get_value('Nozzle', row.nozzle, ['fuel_type', 'nozzle_name']).then(r => {
			if (r.message) {
				const fuel_type = r.message.fuel_type;
				frappe.model.set_value(cdt, cdn, 'fuel_type', fuel_type);

				if (fuel_type && frm.doc.petrol_pump) {
					frappe.call({
						method: 'petrol_pump_v2.petrol_pump_v2.doctype.day_closing.day_closing.get_current_fuel_rate',
						args: {
							fuel_type: fuel_type,
							petrol_pump: frm.doc.petrol_pump,
							reading_date: frm.doc.test_date || frappe.datetime.get_today()
						},
						callback: function (pr) {
							const rate = pr.message || 0;
							frappe.model.set_value(cdt, cdn, 'rate', rate);
							frappe.model.set_value(cdt, cdn, 'amount', flt(row.test_liters) * flt(rate));
						}
					});
				}
			}
		});
	},

	test_liters(frm, cdt, cdn) {
		const row = locals[cdt][cdn];
		if (flt(row.test_liters) <= 0) {
			frappe.msgprint(__('Test Liters must be greater than 0'), 'Validation Error');
			frappe.model.set_value(cdt, cdn, 'test_liters', 1);
		}
		frappe.model.set_value(cdt, cdn, 'amount', flt(row.test_liters) * flt(row.rate));
	}
});
