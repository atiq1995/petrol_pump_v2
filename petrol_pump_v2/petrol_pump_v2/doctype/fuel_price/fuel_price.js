frappe.ui.form.on('Fuel Price', {
	petrol_pump(frm) {
		if (!frm.doc.petrol_pump) return;

		// Clear existing rows
		frm.clear_table('fuel_prices');

		// Get distinct fuel types from Fuel Tanks for this pump
		frappe.call({
			method: 'frappe.client.get_list',
			args: {
				doctype: 'Fuel Tank',
				filters: { petrol_pump: frm.doc.petrol_pump },
				fields: ['fuel_type'],
				group_by: 'fuel_type',
				order_by: 'fuel_type asc'
			},
			callback: function (r) {
				if (r.message && r.message.length > 0) {
					r.message.forEach(function (tank) {
						if (tank.fuel_type) {
							let row = frm.add_child('fuel_prices');
							row.fuel_type = tank.fuel_type;
							row.price_per_liter = 0;
						}
					});
					frm.refresh_field('fuel_prices');
				} else {
					frappe.msgprint(__('No Fuel Tanks found for this Petrol Pump. Please create Fuel Tanks first.'));
				}
			}
		});
	}
});
