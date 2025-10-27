frappe.ui.form.on('Fuel Testing', {
	refresh(frm) {
		if (frm.doc.petrol_pump && !frm.doc.fuel_testing_details.length) {
			frm.trigger('populate_nozzles');
		}
	},
	
	petrol_pump(frm) {
		frm.clear_table('fuel_testing_details');
		frm.refresh_field('fuel_testing_details');
		frm.trigger('populate_nozzles');
	},
	
	populate_nozzles(frm) {
		if (frm.doc.petrol_pump) {
			frm.call('get_available_nozzles').then(r => {
				if (r.message) {
					frm.clear_table('fuel_testing_details');
					r.message.forEach(nozzle_data => {
						frm.add_child('fuel_testing_details', nozzle_data);
					});
					frm.refresh_field('fuel_testing_details');
				}
			});
		}
	},
	
	onload(frm) {
		frm.fields_dict.fuel_testing_details.grid.get_field('nozzle_number').get_query = function(doc, cdt, cdn) {
			const row = locals[cdt][cdn];
			return {
				query: 'petrol_pump_v2.petrol_pump_v2.petrol_pump_v2.doctype.fuel_testing.fuel_testing.get_nozzle_options',
				filters: {
					dispenser: row.dispenser
				}
			};
		};
	}
});

frappe.ui.form.on('Fuel Testing Detail', {
	dispenser(frm, cdt, cdn) {
		const row = locals[cdt][cdn];
		row.nozzle_number = '';
		row.fuel_type = '';
		row.rate = 0;
		row.amount = 0;
		frm.refresh_field('fuel_testing_details');
		set_nozzle_options(frm, cdt, cdn);
	},
	
	nozzle_number(frm, cdt, cdn) {
		const row = locals[cdt][cdn];
		if (!row.dispenser || !row.nozzle_number) return;

		frappe.call({
			method: 'frappe.client.get',
			args: { doctype: 'Dispenser', name: row.dispenser },
		}).then(r => {
			const nozzle = (r.message?.nozzles || []).find(n => n.nozzle_number === row.nozzle_number);
			if (nozzle) {
				row.fuel_type = nozzle.fuel_type || '';
			}
			if (row.fuel_type) {
				frappe.db.get_value('Fuel Price',
					{ fuel_type: row.fuel_type, is_active: 1, effective_from: ['<=', frm.doc.test_date || frappe.datetime.now_datetime()] },
					'price_per_liter'
				).then(pr => {
					row.rate = pr?.message?.price_per_liter || 0;
					frm.refresh_field('fuel_testing_details');
					calculate_testing_row(row);
				});
			} else {
				frm.refresh_field('fuel_testing_details');
				calculate_testing_row(row);
			}
		});
	},
	
	test_liters(frm, cdt, cdn) {
		const row = locals[cdt][cdn];
		if (flt(row.test_liters) <= 0) {
			frappe.msgprint(__('Test Liters must be greater than 0'), 'Validation Error');
			row.test_liters = 1;
		}
		calculate_testing_row(row);
		frm.refresh_field('fuel_testing_details');
	},
	
	form_render(frm, cdt, cdn) {
		const row = locals[cdt][cdn];
		if (row.dispenser) {
			set_nozzle_options(frm, cdt, cdn);
		}
	}
});

function calculate_testing_row(row) {
	row.amount = flt(row.test_liters) * flt(row.rate);
}

function set_nozzle_options(frm, cdt, cdn) {
	const row = locals[cdt][cdn];
	if (!row.dispenser) {
		frm.fields_dict.fuel_testing_details.grid.update_docfield_property('nozzle_number', 'options', '');
		if (frm.fields_dict.fuel_testing_details.grid.get_row(row.name).get_field('nozzle_number').df) {
			frm.fields_dict.fuel_testing_details.grid.get_row(row.name).get_field('nozzle_number').df.options = '';
		}
		return;
	}

	frappe.call({
		method: 'frappe.client.get',
		args: { doctype: 'Dispenser', name: row.dispenser },
		callback: function(r) {
			if (r.message && r.message.nozzles) {
				const nozzles = r.message.nozzles
					.filter(n => n.is_active)
					.map(n => n.nozzle_number);
				const options_str = nozzles.join('\n');

				frm.fields_dict.fuel_testing_details.grid.update_docfield_property('nozzle_number', 'options', options_str);
				if (frm.fields_dict.fuel_testing_details.grid.get_row(row.name).get_field('nozzle_number').df) {
					frm.fields_dict.fuel_testing_details.grid.get_row(row.name).get_field('nozzle_number').df.options = options_str;
				}
			} else {
				frm.fields_dict.fuel_testing_details.grid.update_docfield_property('nozzle_number', 'options', '');
				if (frm.fields_dict.fuel_testing_details.grid.get_row(row.name).get_field('nozzle_number').df) {
					frm.fields_dict.fuel_testing_details.grid.get_row(row.name).get_field('nozzle_number').df.options = '';
				}
			}
		}
	});
}
