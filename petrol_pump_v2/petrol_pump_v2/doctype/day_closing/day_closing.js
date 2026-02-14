frappe.ui.form.on('Day Closing', {
  setup(frm) {
    // Filter expense_account to show only Indirect Expenses accounts
    frm.set_query('expense_account', 'expenses', function() {
      return {
        query: 'petrol_pump_v2.petrol_pump_v2.doctype.day_closing.day_closing.get_indirect_expense_accounts'
      };
    });

    // Filter bank_account in card_sales to match selected bank
    frm.set_query('bank_account', 'card_sales', function(doc, cdt, cdn) {
      const row = frappe.get_doc(cdt, cdn);
      const filters = {};
      if (row.bank) {
        filters.bank = row.bank;
      }
      return { filters: filters };
    });
  },
  refresh(frm) {
    if (frm.is_new() && frm.doc.petrol_pump) {
      populate_nozzles(frm);
      show_available_stock(frm);
    }
    // Enable inline editing on nozzle_readings grid and disable row-form on click
    if (frm.fields_dict['nozzle_readings'] && frm.fields_dict['nozzle_readings'].grid) {
      const grid = frm.fields_dict['nozzle_readings'].grid;
      grid.editable_fields = [
        {fieldname: 'nozzle_number', columns: 3},
        {fieldname: 'current_reading', columns: 2}
      ];
      // Disable opening the row form on row click; only open when Edit icon is used
      const original_open = grid.open_grid_row;
      grid.open_grid_row = function(row) {
        if (row && row.open_from_button) {
          // allow open when explicitly from Edit button
          return original_open.call(this, row);
        }
        // otherwise skip to keep inline editing
      };
    }
    
    // Recalculate amounts for credit details on refresh
    if (frm.doc.credit_details && frm.doc.credit_details.length > 0) {
      frm.doc.credit_details.forEach((row, idx) => {
        if (row.liters && row.rate) {
          const cdn = row.name || row.idx;
          calculate_amount(frm, 'Day Closing Credit Detail', cdn);
        }
      });
    }
    
    // Recalculate total expenses on refresh
    calculate_total_expenses(frm);
  },
  petrol_pump(frm) {
    if (!frm.doc.petrol_pump) return;
    frm.set_value('nozzle_readings', []);
    populate_nozzles(frm);
    show_available_stock(frm);
  },
  reading_date(frm) {
    // When reading date changes, refresh nozzles to get correct previous reading
    if (frm.doc.petrol_pump && frm.doc.reading_date) {
      frm.set_value('nozzle_readings', []);
      populate_nozzles(frm);
    }
  },
});

// Handle credit details child table
frappe.ui.form.on('Day Closing Credit Detail', {
  fuel_type(frm, cdt, cdn) {
    const row = frappe.get_doc(cdt, cdn);
    if (row.fuel_type) {
      const reading_date = frm.doc.reading_date || frappe.datetime.get_today();
      // Fetch current rate for the selected fuel type
      frappe.call({
        method: 'petrol_pump_v2.petrol_pump_v2.doctype.day_closing.day_closing.get_current_fuel_rate',
        args: {
          fuel_type: row.fuel_type,
          petrol_pump: frm.doc.petrol_pump,
          reading_date: reading_date
        }
      }).then((r) => {
        if (r.message) {
          frappe.model.set_value(cdt, cdn, 'rate', r.message);
          // Wait a bit then calculate amount
          setTimeout(() => {
            calculate_amount(frm, cdt, cdn);
          }, 100);
        }
      });
    } else {
      // Clear rate and amount if fuel_type is cleared
      frappe.model.set_value(cdt, cdn, 'rate', null);
      frappe.model.set_value(cdt, cdn, 'amount', 0);
    }
  },
  liters(frm, cdt, cdn) {
    calculate_amount(frm, cdt, cdn);
    // Also trigger parent calculation
    if (frm.doc.doctype === 'Day Closing') {
      frm.save();
    }
  },
  rate(frm, cdt, cdn) {
    calculate_amount(frm, cdt, cdn);
  }
});

// Handle expenses child table
frappe.ui.form.on('Day Closing Expense Detail', {
  amount(frm, cdt, cdn) {
    calculate_total_expenses(frm);
  },
  day_closing_expense_detail_add(frm) {
    calculate_total_expenses(frm);
  },
  day_closing_expense_detail_remove(frm) {
    calculate_total_expenses(frm);
  }
});

// Handle card/POS sales child table
frappe.ui.form.on('Day Closing Card Detail', {
  bank(frm, cdt, cdn) {
    // Clear bank_account when bank changes so user picks the correct one
    frappe.model.set_value(cdt, cdn, 'bank_account', '');
  },
  amount(frm, cdt, cdn) {
    calculate_total_card_amount(frm);
  },
  day_closing_card_detail_add(frm) {
    calculate_total_card_amount(frm);
  },
  day_closing_card_detail_remove(frm) {
    calculate_total_card_amount(frm);
  }
});

// Helper function to calculate amount
function calculate_amount(frm, cdt, cdn) {
  const row = frappe.get_doc(cdt, cdn);
  const liters = parseFloat(row.liters || 0);
  const rate = parseFloat(row.rate || 0);
  
  if (liters > 0 && rate > 0) {
    const amount = liters * rate;
    frappe.model.set_value(cdt, cdn, 'amount', amount);
  } else {
    frappe.model.set_value(cdt, cdn, 'amount', 0);
  }
  
  // Refresh the field to show updated value
  frm.refresh_field('credit_details');
}

function populate_nozzles(frm) {
  const reading_date = frm.doc.reading_date || frappe.datetime.get_today();
  frappe.call({
    method: 'petrol_pump_v2.petrol_pump_v2.doctype.day_closing.day_closing.get_active_nozzles_for_day_closing',
    args: { 
      petrol_pump: frm.doc.petrol_pump,
      reading_date: reading_date
    },
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

function calculate_total_expenses(frm) {
  let total = 0;
  if (frm.doc.expenses && frm.doc.expenses.length > 0) {
    frm.doc.expenses.forEach((row) => {
      total += parseFloat(row.amount || 0);
    });
  }
  frm.set_value('total_expenses', total);
  frm.refresh_field('total_expenses');
}

function calculate_total_card_amount(frm) {
  let total = 0;
  if (frm.doc.card_sales && frm.doc.card_sales.length > 0) {
    frm.doc.card_sales.forEach((row) => {
      total += parseFloat(row.amount || 0);
    });
  }
  frm.set_value('card_amount', total);
  frm.refresh_field('card_amount');
}
