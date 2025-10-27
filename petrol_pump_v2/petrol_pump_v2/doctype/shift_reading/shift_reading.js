frappe.ui.form.on('Shift Reading', {
  refresh(frm) {
    if (!frm.is_new()) return;
    if (frm.doc.petrol_pump) {
      populate_all_nozzles(frm);
    }
  },
  petrol_pump(frm) {
    if (frm.doc.petrol_pump) {
      // reset and repopulate
      frm.set_value('nozzle_readings', []);
      populate_all_nozzles(frm);
    }
  },
});

function populate_all_nozzles(frm) {
  frappe.call({
    method: 'petrol_pump_v2.petrol_pump_v2.doctype.shift_reading.shift_reading.get_active_nozzles',
    args: { petrol_pump: frm.doc.petrol_pump },
  }).then((r) => {
    const rows = r.message || [];
    (rows || []).forEach((row) => {
      frm.add_child('nozzle_readings', row);
    });
    frm.refresh_field('nozzle_readings');
  });
}

function set_nozzle_options(frm, cdn, options) {
  const grid = frm.fields_dict.nozzle_readings.grid;
  try {
    grid.update_docfield_property('nozzle_number', 'options', options || '');
  } catch (e) {}
  const row = grid.get_row(cdn);
  if (row && row.grid_form && row.grid_form.fields_dict && row.grid_form.fields_dict.nozzle_number) {
    row.grid_form.fields_dict.nozzle_number.df.options = options || '';
    row.grid_form.refresh_fields();
  }
  frm.refresh_field('nozzle_readings');
}

function populate_nozzle_options_for_row(frm, cdt, cdn) {
  const row = locals[cdt][cdn];
  if (!row.dispenser) {
    set_nozzle_options(frm, cdn, '');
    return;
  }
  frappe.call({
    method: 'frappe.client.get',
    args: { doctype: 'Dispenser', name: row.dispenser },
  }).then((r) => {
    const nozzles = (r.message?.nozzles || []).filter(n => !!n.is_active).map(n => n.nozzle_number);
    const options = (nozzles || []).join('\n');
    set_nozzle_options(frm, cdn, options);
  });
}

frappe.ui.form.on('Nozzle Reading Detail', {
  form_render(frm, cdt, cdn) {
    populate_nozzle_options_for_row(frm, cdt, cdn);
  },
  dispenser(frm, cdt, cdn) {
    const row = locals[cdt][cdn];
    row.nozzle_number = '';
    row.fuel_type = '';
    row.previous_reading = 0;
    row.rate = 0;
    row.amount = 0;
    populate_nozzle_options_for_row(frm, cdt, cdn);
  },
  nozzle_number(frm, cdt, cdn) {
    const row = locals[cdt][cdn];
    if (!row.dispenser || !row.nozzle_number) return;
    frappe.call({
      method: 'frappe.client.get',
      args: { doctype: 'Dispenser', name: row.dispenser },
    }).then((r) => {
      const noz = (r.message?.nozzles || []).find(n => n.nozzle_number === row.nozzle_number);
      if (noz) {
        row.fuel_type = noz.fuel_type || '';
        row.previous_reading = noz.last_reading || 0;
      }
      if (row.fuel_type) {
        frappe.call({
          method: 'frappe.client.get_list',
          args: {
            doctype: 'Fuel Price',
            filters: { fuel_type: row.fuel_type, is_active: 1 },
            fields: ['price_per_liter', 'effective_from'],
            order_by: 'effective_from desc',
            limit_page_length: 1,
          },
        }).then((pr) => {
          row.rate = (pr.message && pr.message[0] && pr.message[0].price_per_liter) || 0;
          row.dispensed_liters = (row.current_reading || 0) - (row.previous_reading || 0);
          row.amount = (row.dispensed_liters || 0) * (row.rate || 0);
          frm.refresh_field('nozzle_readings');
        });
      } else {
        frm.refresh_field('nozzle_readings');
      }
    });
  },
  current_reading(frm, cdt, cdn) {
    const row = locals[cdt][cdn];
    if (row.current_reading < row.previous_reading) {
      frappe.msgprint(__('Current Reading cannot be less than Previous Reading'));
      row.current_reading = row.previous_reading;
    }
    row.dispensed_liters = (row.current_reading || 0) - (row.previous_reading || 0);
    row.amount = (row.dispensed_liters || 0) * (row.rate || 0);
    frm.refresh_field('nozzle_readings');
  },
});
