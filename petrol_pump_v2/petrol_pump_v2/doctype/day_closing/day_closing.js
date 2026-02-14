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
    if (frm.is_new() && frm.doc.petrol_pump && (!frm.doc.nozzle_readings || frm.doc.nozzle_readings.length === 0)) {
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
    fetch_previous_cash(frm);
  },
  reading_date(frm) {
    // When reading date changes, refresh nozzles to get correct previous reading
    if (frm.doc.petrol_pump && frm.doc.reading_date) {
      frm.set_value('nozzle_readings', []);
      populate_nozzles(frm);
      fetch_previous_cash(frm);
    }
  },
  cash_amount(frm) {
    calculate_cash_reconciliation(frm);
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
    calculate_credit_totals(frm);
    calculate_cash_reconciliation(frm);
  },
  rate(frm, cdt, cdn) {
    calculate_amount(frm, cdt, cdn);
    calculate_credit_totals(frm);
    calculate_cash_reconciliation(frm);
  },
  credit_details_add(frm) {
    calculate_credit_totals(frm);
    calculate_cash_reconciliation(frm);
  },
  credit_details_remove(frm) {
    calculate_credit_totals(frm);
    calculate_cash_reconciliation(frm);
  }
});

// Handle expenses child table
frappe.ui.form.on('Day Closing Expense Detail', {
  amount(frm, cdt, cdn) {
    calculate_total_expenses(frm);
    calculate_cash_reconciliation(frm);
  },
  day_closing_expense_detail_add(frm) {
    calculate_total_expenses(frm);
    calculate_cash_reconciliation(frm);
  },
  day_closing_expense_detail_remove(frm) {
    calculate_total_expenses(frm);
    calculate_cash_reconciliation(frm);
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
    calculate_cash_reconciliation(frm);
  },
  day_closing_card_detail_add(frm) {
    calculate_total_card_amount(frm);
    calculate_cash_reconciliation(frm);
  },
  day_closing_card_detail_remove(frm) {
    calculate_total_card_amount(frm);
    calculate_cash_reconciliation(frm);
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

function calculate_credit_totals(frm) {
  let total_liters = 0;
  let total_amount = 0;
  if (frm.doc.credit_details && frm.doc.credit_details.length > 0) {
    frm.doc.credit_details.forEach((row) => {
      total_liters += parseFloat(row.liters || 0);
      total_amount += parseFloat(row.amount || 0);
    });
  }
  frm.set_value('credit_sales_liters', total_liters);
  frm.set_value('credit_amount', total_amount);
  frm.refresh_field('credit_sales_liters');
  frm.refresh_field('credit_amount');
}

function calculate_cash_reconciliation(frm) {
  const previous_cash = parseFloat(frm.doc.previous_cash || 0);
  const cash_amount = parseFloat(frm.doc.cash_amount || 0);
  const card_amount = parseFloat(frm.doc.card_amount || 0);
  const total_sales = parseFloat(frm.doc.total_sales || 0);
  const credit_amount = parseFloat(frm.doc.credit_amount || 0);
  const total_expenses = parseFloat(frm.doc.total_expenses || 0);

  // Total Payments Received = Previous Cash + Cash Collected + Card
  const total_payments_received = previous_cash + cash_amount + card_amount;
  // Expected to Collect = Total Sales - Credit Sales
  const expected_to_collect = total_sales - credit_amount;
  // Expected Collection = Previous Cash + Expected to Collect - Expenses
  const expected_collection = previous_cash + expected_to_collect - total_expenses;
  // Net Cash After Expenses = Total Payments Received
  const net_cash_after_expenses = total_payments_received;
  // Cash Variance = Actual - Expected (should be 0 if correct)
  const cash_variance = total_payments_received - expected_collection;

  frm.set_value('total_payments_received', total_payments_received);
  frm.set_value('expected_to_collect', expected_to_collect);
  frm.set_value('expected_collection', expected_collection);
  frm.set_value('net_cash_after_expenses', net_cash_after_expenses);
  frm.set_value('cash_variance', cash_variance);

  frm.refresh_fields();
}

function fetch_previous_cash(frm) {
  if (!frm.doc.petrol_pump) return;
  frappe.call({
    method: 'petrol_pump_v2.petrol_pump_v2.doctype.day_closing.day_closing.get_previous_cash',
    args: {
      petrol_pump: frm.doc.petrol_pump,
      reading_date: frm.doc.reading_date || frappe.datetime.get_today()
    },
  }).then((r) => {
    frm.set_value('previous_cash', r.message || 0);
    calculate_cash_reconciliation(frm);
  });
}
