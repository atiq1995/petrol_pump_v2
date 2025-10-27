import frappe
from frappe.model.document import Document
from frappe.utils import flt, nowdate, now_datetime

class DayClosing(Document):
    def validate(self):
        """Validate stock availability and price for all nozzle readings"""
        if not self.petrol_pump:
            return
        
        # Validate prices (Blueprint requirement: No submit if price missing/zero)
        self.validate_prices()
        
        # Validate stock availability
        self.validate_stock_availability()
    
    def validate_prices(self):
        """Ensure all nozzle readings have valid prices"""
        for d in self.nozzle_readings or []:
            if d.dispensed_liters and d.dispensed_liters > 0:
                if not d.rate or flt(d.rate) <= 0:
                    frappe.throw(
                        f"Price is missing or zero for {d.fuel_type} on Dispenser {d.dispenser}, Nozzle {d.nozzle_number}. "
                        "Please ensure active Fuel Price exists for the reading date."
                    )
    
    def validate_stock_availability(self):
        """Block save if issuing would deplete stock to zero or negative.
        Sums dispensed liters by fuel type and compares against available qty across
        all tank warehouses for this petrol pump for that fuel type.
        """
        # sum by fuel type
        issue_by_fuel = {}
        for d in self.nozzle_readings or []:
            if d.dispensed_liters and d.dispensed_liters > 0 and d.fuel_type:
                issue_by_fuel[d.fuel_type] = issue_by_fuel.get(d.fuel_type, 0) + flt(d.dispensed_liters)

        if not issue_by_fuel:
            return

        # available by fuel type = sum of Bin across all tank warehouses for this pump
        for fuel_type, to_issue in issue_by_fuel.items():
            total_available = 0.0
            tanks = frappe.get_all(
                "Fuel Tank",
                filters={"petrol_pump": self.petrol_pump, "fuel_type": fuel_type},
                fields=["warehouse"],
            )
            for t in tanks:
                if not t.warehouse:
                    continue
                qty = frappe.db.get_value(
                    "Bin",
                    {"warehouse": t.warehouse, "item_code": fuel_type},
                    "actual_qty",
                ) or 0
                total_available += flt(qty)

            remaining = total_available - flt(to_issue)
            # Disallow zero or negative remaining as requested
            if remaining <= 0:
                frappe.throw(
                    f"Insufficient stock for Fuel Type {fuel_type}. Available: {total_available}, Issue: {to_issue}. This would leave {remaining} (<= 0)."
                )
    def before_save(self):
        self.calculate_readings()
        self.calculate_cash_reconciliation()

    def on_submit(self):
        self.create_stock_entry()
        self.create_sales_invoice()
        self.update_nozzle_last_readings()
        self.set_approval_status()
    
    def on_cancel(self):
        """Cancel all auto-created transactions when Day Closing is cancelled"""
        self.cancel_linked_transactions()
        self.revert_nozzle_readings()
    
    def set_approval_status(self):
        """Set approval status based on cash variance"""
        if abs(flt(self.cash_variance)) > 500:  # Configurable threshold
            self.db_set('workflow_state', 'Pending Approval')
        else:
            self.db_set('workflow_state', 'Approved')

    def get_current_rate(self, fuel_type):
        if not fuel_type:
            return 0
        rate = frappe.db.sql(
            """
            SELECT price_per_liter 
            FROM `tabFuel Price` 
            WHERE fuel_type = %s AND is_active = 1 AND effective_from <= %s
            ORDER BY effective_from DESC LIMIT 1
            """,
            (fuel_type, now_datetime()),
        )
        return rate[0][0] if rate else 0

    def calculate_readings(self):
        total_sales = 0
        total_liters = 0
        for d in self.nozzle_readings:
            d.dispensed_liters = flt(d.current_reading) - flt(d.previous_reading)
            if not d.rate:
                d.rate = self.get_current_rate(d.fuel_type)
            d.amount = flt(d.dispensed_liters) * flt(d.rate)
            total_sales += flt(d.amount)
            total_liters += flt(d.dispensed_liters)
        self.total_sales = total_sales
        self.total_liters = total_liters

    def calculate_cash_reconciliation(self):
        """Calculate cash reconciliation totals and variance"""
        # Calculate total payments received (cash + card)
        self.total_payments_received = flt(self.cash_amount) + flt(self.card_amount)
        
        # Expected collection = Total Sales - Credit Sales
        self.expected_collection = flt(self.total_sales) - flt(self.credit_amount)
        
        # Cash variance = Actual - Expected
        self.cash_variance = flt(self.total_payments_received) - flt(self.expected_collection)

    def create_stock_entry(self):
        fuel_consumption = {}
        for d in self.nozzle_readings:
            if d.dispensed_liters > 0:
                fuel_consumption[d.fuel_type] = fuel_consumption.get(d.fuel_type, 0) + d.dispensed_liters
        if not fuel_consumption:
            return
        se = frappe.new_doc("Stock Entry")
        se.stock_entry_type = "Material Issue"
        se.purpose = "Material Issue"
        se.company = frappe.db.get_value("Petrol Pump", self.petrol_pump, "company")
        se.set_posting_time = 1
        se.posting_date = self.reading_date or nowdate()
        for fuel_type, liters in fuel_consumption.items():
            warehouse = frappe.db.get_value(
                "Fuel Tank",
                {"petrol_pump": self.petrol_pump, "fuel_type": fuel_type},
                "warehouse",
            )
            if warehouse:
                # Get actual valuation rate for proper COGS tracking
                valuation_rate = self.get_valuation_rate(fuel_type, warehouse)
                
                se.append("items", {
                    "s_warehouse": warehouse,
                    "item_code": fuel_type,
                    "qty": liters,
                    "basic_rate": valuation_rate,
                    "conversion_factor": 1.0,
                })
        if se.items:
            se.insert()
            se.submit()
            # Store reference for cancellation handling
            self.db_set('stock_entry_ref', se.name)
            frappe.msgprint(f"Stock Entry {se.name} created for day closing consumption")
    
    def get_valuation_rate(self, item_code, warehouse):
        """Get current valuation rate for accurate COGS tracking"""
        valuation_rate = frappe.db.get_value(
            "Stock Ledger Entry",
            {
                "item_code": item_code,
                "warehouse": warehouse,
                "is_cancelled": 0
            },
            "valuation_rate",
            order_by="posting_date desc, posting_time desc, creation desc"
        )
        return flt(valuation_rate) if valuation_rate else 0

    def create_sales_invoice(self):
        """Create consolidated Sales Invoice for daily cash sales"""
        if not self.total_sales or self.total_sales <= 0:
            return
        
        # Get company and default customer
        company = frappe.db.get_value("Petrol Pump", self.petrol_pump, "company")
        
        # Get company's default currency
        company_currency = frappe.db.get_value("Company", company, "default_currency")
        
        # Check if Cash Customer exists, create if not
        cash_customer = self.get_or_create_cash_customer(company)
        
        # Group sales by fuel type
        fuel_sales = {}
        for d in self.nozzle_readings:
            if d.dispensed_liters > 0 and d.fuel_type:
                if d.fuel_type not in fuel_sales:
                    fuel_sales[d.fuel_type] = {
                        'qty': 0,
                        'rate': d.rate,
                        'amount': 0
                    }
                fuel_sales[d.fuel_type]['qty'] += flt(d.dispensed_liters)
                fuel_sales[d.fuel_type]['amount'] += flt(d.amount)
        
        if not fuel_sales:
            return
        
        # Create Sales Invoice
        si = frappe.new_doc("Sales Invoice")
        si.customer = cash_customer
        si.company = company
        si.currency = company_currency
        si.posting_date = self.reading_date or nowdate()
        si.set_posting_time = 1
        si.due_date = self.reading_date or nowdate()
        
        # Add items for each fuel type
        for fuel_type, data in fuel_sales.items():
            si.append("items", {
                "item_code": fuel_type,
                "qty": data['qty'],
                "rate": data['rate'],
                "amount": data['amount'],
                "uom": "Litre"
            })
        
        si.insert()
        si.submit()
        # Store reference for cancellation handling
        self.db_set('sales_invoice_ref', si.name)
        
        frappe.msgprint(f"Sales Invoice {si.name} created for total sales of {self.total_sales}")
        
        # Create Payment Entry for cash/UPI/card payments
        if flt(self.total_payments_received) > 0:
            self.create_payment_entry(si, company)
    
    def get_or_create_cash_customer(self, company):
        """Get or create a default Cash Customer"""
        customer_name = "Cash Customer"
        
        if not frappe.db.exists("Customer", customer_name):
            # Get company's default currency
            company_currency = frappe.db.get_value("Company", company, "default_currency")
            
            customer = frappe.new_doc("Customer")
            customer.customer_name = customer_name
            customer.customer_type = "Individual"
            customer.customer_group = frappe.db.get_single_value("Selling Settings", "customer_group") or "Individual"
            customer.territory = frappe.db.get_single_value("Selling Settings", "territory") or "All Territories"
            customer.default_currency = company_currency
            customer.insert(ignore_permissions=True)
            frappe.db.commit()
        
        return customer_name
    
    def create_payment_entry(self, sales_invoice, company):
        """Create Payment Entry for cash collection"""
        if flt(self.total_payments_received) <= 0:
            return
        
        # Get company's default currency
        company_currency = frappe.db.get_value("Company", company, "default_currency")
        
        # Get default accounts
        mode_of_payment = frappe.db.get_value("Mode of Payment", {"type": "Cash"}, "name") or "Cash"
        
        # Get default receivable account
        default_receivable_account = frappe.get_cached_value("Company", company, "default_receivable_account")
        
        # Get cash account from mode of payment account or company default
        cash_account = frappe.db.get_value(
            "Mode of Payment Account",
            {"parent": mode_of_payment, "company": company},
            "default_account"
        )
        if not cash_account:
            cash_account = frappe.get_cached_value("Company", company, "default_cash_account")
        
        pe = frappe.new_doc("Payment Entry")
        pe.payment_type = "Receive"
        pe.party_type = "Customer"
        pe.party = sales_invoice.customer
        pe.company = company
        pe.posting_date = self.reading_date or nowdate()
        
        # Set currency and exchange rate
        pe.paid_from_account_currency = company_currency
        pe.paid_to_account_currency = company_currency
        pe.source_exchange_rate = 1.0
        pe.target_exchange_rate = 1.0
        
        # Set accounts
        pe.paid_from = default_receivable_account
        pe.paid_to = cash_account
        
        # Set amounts
        pe.paid_amount = flt(self.total_payments_received)
        pe.received_amount = flt(self.total_payments_received)
        pe.mode_of_payment = mode_of_payment
        pe.reference_no = self.name
        pe.reference_date = self.reading_date or nowdate()
        
        # Link to sales invoice
        pe.append("references", {
            "reference_doctype": "Sales Invoice",
            "reference_name": sales_invoice.name,
            "total_amount": sales_invoice.grand_total,
            "outstanding_amount": sales_invoice.outstanding_amount,
            "allocated_amount": min(flt(self.total_payments_received), sales_invoice.outstanding_amount)
        })
        
        pe.insert()
        pe.submit()
        # Store reference for cancellation handling
        self.db_set('payment_entry_ref', pe.name)
        
        frappe.msgprint(f"Payment Entry {pe.name} created for {self.total_payments_received}")

    def update_nozzle_last_readings(self):
        """Update last_reading in nozzles when Day Closing is submitted"""
        for d in self.nozzle_readings:
            frappe.db.sql(
                """
                UPDATE `tabDispenser Nozzle Detail` 
                SET last_reading = %s 
                WHERE parent = %s AND nozzle_number = %s
                """,
                (d.current_reading, d.dispenser, d.nozzle_number),
            )
    
    def revert_nozzle_readings(self):
        """Revert nozzle readings to previous values when Day Closing is cancelled"""
        for d in self.nozzle_readings:
            frappe.db.sql(
                """
                UPDATE `tabDispenser Nozzle Detail` 
                SET last_reading = %s 
                WHERE parent = %s AND nozzle_number = %s
                """,
                (d.previous_reading, d.dispenser, d.nozzle_number),
            )
        frappe.msgprint("Nozzle readings reverted to previous values")
    
    def cancel_linked_transactions(self):
        """Cancel all auto-created transactions (Stock Entry, Sales Invoice, Payment Entry)"""
        errors = []
        
        # Cancel Payment Entry first (must be done before Sales Invoice)
        if self.payment_entry_ref:
            try:
                pe = frappe.get_doc("Payment Entry", self.payment_entry_ref)
                if pe.docstatus == 1:  # Only cancel if submitted
                    pe.cancel()
                    frappe.msgprint(f"Payment Entry {self.payment_entry_ref} cancelled")
            except Exception as e:
                errors.append(f"Payment Entry {self.payment_entry_ref}: {str(e)}")
        
        # Cancel Sales Invoice
        if self.sales_invoice_ref:
            try:
                si = frappe.get_doc("Sales Invoice", self.sales_invoice_ref)
                if si.docstatus == 1:  # Only cancel if submitted
                    si.cancel()
                    frappe.msgprint(f"Sales Invoice {self.sales_invoice_ref} cancelled")
            except Exception as e:
                errors.append(f"Sales Invoice {self.sales_invoice_ref}: {str(e)}")
        
        # Cancel Stock Entry
        if self.stock_entry_ref:
            try:
                se = frappe.get_doc("Stock Entry", self.stock_entry_ref)
                if se.docstatus == 1:  # Only cancel if submitted
                    se.cancel()
                    frappe.msgprint(f"Stock Entry {self.stock_entry_ref} cancelled")
            except Exception as e:
                errors.append(f"Stock Entry {self.stock_entry_ref}: {str(e)}")
        
        if errors:
            frappe.msgprint(
                f"Some transactions could not be cancelled:<br>" + "<br>".join(errors),
                indicator="orange",
                alert=True
            )
        else:
            frappe.msgprint("All linked transactions cancelled successfully", indicator="green")

@frappe.whitelist()
def get_available_stock(petrol_pump: str):
    if not petrol_pump:
        return []
    rows = []
    tanks = frappe.get_all("Fuel Tank", filters={"petrol_pump": petrol_pump}, fields=["name", "fuel_type", "warehouse"])
    for t in tanks:
        if not t.warehouse:
            continue
        # Use Stock Ledger to get current qty; fallback to 0
        qty = frappe.db.get_value("Bin", {"warehouse": t.warehouse, "item_code": t.fuel_type}, "actual_qty") or 0
        rows.append({
            "tank": t.name,
            "fuel_type": t.fuel_type,
            "warehouse": t.warehouse,
            "qty": flt(qty),
        })
    return rows
