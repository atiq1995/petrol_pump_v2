frappe.ui.form.on('Tank Dip Reading', {
  refresh(frm) {
    if (frm.doc.docstatus === 0 && frm.doc.petrol_pump) {
      frm.add_custom_button(__('Load Tanks'), () => load_tanks(frm));
    }
  },

  petrol_pump(frm) {
    if (!frm.doc.petrol_pump) {
      frm.set_value('tank_readings', []);
      frm.set_value('total_variance', 0);
      return;
    }
    load_tanks(frm);
  },

  reading_date(frm) {
    if (frm.doc.petrol_pump) {
      load_tanks(frm);
    }
  }
});

frappe.ui.form.on('Tank Dip Reading Detail', {
  measured_dip(frm, cdt, cdn) {
    const row = frappe.get_doc(cdt, cdn);
    const measured = parseFloat(row.measured_dip || 0);
    const system = parseFloat(row.system_stock || 0);
    frappe.model.set_value(cdt, cdn, 'difference', measured - system);
    calculate_total_variance(frm);
  },
  tank_readings_add(frm) {
    calculate_total_variance(frm);
  },
  tank_readings_remove(frm) {
    calculate_total_variance(frm);
  }
});

function load_tanks(frm) {
  const existing = {};
  (frm.doc.tank_readings || []).forEach((row) => {
    existing[row.fuel_tank] = {
      measured_dip: row.measured_dip,
      remarks: row.remarks
    };
  });

  frappe.call({
    method: 'petrol_pump_v2.petrol_pump_v2.doctype.tank_dip_reading.tank_dip_reading.get_pump_tank_rows',
    args: {
      petrol_pump: frm.doc.petrol_pump,
      reading_date: frm.doc.reading_date || frappe.datetime.get_today()
    }
  }).then((r) => {
    const rows = r.message || [];
    frm.set_value('tank_readings', []);

    rows.forEach((row) => {
      const prev = existing[row.fuel_tank] || {};
      const child = frm.add_child('tank_readings', {
        fuel_tank: row.fuel_tank,
        fuel_type: row.fuel_type,
        warehouse: row.warehouse,
        system_stock: row.system_stock,
        measured_dip: prev.measured_dip || 0,
        remarks: prev.remarks || ''
      });

      child.difference = (parseFloat(child.measured_dip || 0) - parseFloat(child.system_stock || 0));
    });

    frm.refresh_field('tank_readings');
    calculate_total_variance(frm);
  });
}

function calculate_total_variance(frm) {
  let total = 0;
  (frm.doc.tank_readings || []).forEach((row) => {
    total += parseFloat(row.difference || 0);
  });
  frm.set_value('total_variance', total);
}
