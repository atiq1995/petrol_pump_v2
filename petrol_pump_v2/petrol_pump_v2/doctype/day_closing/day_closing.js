frappe.ui.form.on('Day Closing', {
  refresh(frm) {
    if (frm.is_new() && frm.doc.petrol_pump) {
      populate_nozzles(frm);
      show_available_stock(frm);
    }
  },
  petrol_pump(frm) {
    if (!frm.doc.petrol_pump) return;
    frm.set_value('nozzle_readings', []);
    populate_nozzles(frm);
    show_available_stock(frm);
  },
});

function populate_nozzles(frm) {
  frappe.call({
    method: 'petrol_pump_v2.petrol_pump_v2.doctype.shift_reading.shift_reading.get_active_nozzles',
    args: { petrol_pump: frm.doc.petrol_pump },
  }).then((r) => {
    const rows = r.message || [];
    (rows || []).forEach((row) => frm.add_child('nozzle_readings', row));
    frm.refresh_field('nozzle_readings');
  });
}

function show_available_stock(frm) {
  frappe.call({
    method: 'petrol_pump_v2.petrol_pump_v2.doctype.day_closing.day_closing.get_available_stock',
    args: { petrol_pump: frm.doc.petrol_pump },
  }).then((r) => {
    const rows = r.message || [];
    const text = (rows || []).map(x => `${x.tank} (${x.fuel_type}) @ ${x.warehouse}: ${x.qty}`).join('\n');
    frm.set_value('available_stock', text || '');
  });
}
