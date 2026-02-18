import frappe
from frappe.model.document import Document
from frappe.utils import flt, nowdate, now_datetime

class DayClosing(Document):
    def validate(self):
        """Runs on save and submit. Only basic checks here so user can save freely."""
        if not self.petrol_pump:
            return

        self.validate_prices()

    def before_submit(self):
        """Heavy validations that should only block submit, not save."""
        self.validate_stock_availability()
        self.validate_credit_sales()
    
    def validate_prices(self):
        """Ensure all nozzle readings have valid prices"""
        for d in self.nozzle_readings or []:
            if d.dispensed_liters and d.dispensed_liters > 0:
                if not d.rate or flt(d.rate) <= 0:
                    frappe.throw(
                        f"Price is missing or zero for {d.fuel_type} on Nozzle {d.nozzle_number}. "
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
    def validate_credit_sales(self):
        """Validate that credit sales per fuel type don't exceed nozzle sales for that fuel type."""
        # Sum nozzle sales by fuel type
        nozzle_by_fuel = {}
        for d in self.nozzle_readings or []:
            liters = flt(d.current_reading) - flt(d.previous_reading)
            if liters > 0 and d.fuel_type:
                if d.fuel_type not in nozzle_by_fuel:
                    nozzle_by_fuel[d.fuel_type] = {"liters": 0, "amount": 0}
                rate = flt(d.rate) or self.get_current_rate(d.fuel_type)
                nozzle_by_fuel[d.fuel_type]["liters"] += liters
                nozzle_by_fuel[d.fuel_type]["amount"] += liters * rate

        # Sum credit sales by fuel type
        credit_by_fuel = {}
        for d in getattr(self, "credit_details", []) or []:
            ft = getattr(d, "fuel_type", None)
            if ft and flt(getattr(d, "liters", 0)) > 0:
                if ft not in credit_by_fuel:
                    credit_by_fuel[ft] = {"liters": 0, "amount": 0}
                credit_by_fuel[ft]["liters"] += flt(d.liters)
                credit_by_fuel[ft]["amount"] += flt(d.amount)

        for fuel_type, credit_data in credit_by_fuel.items():
            nozzle_data = nozzle_by_fuel.get(fuel_type)
            if not nozzle_data:
                frappe.throw(
                    f"Credit sale has Fuel Type <b>{fuel_type}</b> but no nozzle readings exist for this fuel type. "
                    "Please check your credit sales entries."
                )
            if credit_data["liters"] > nozzle_data["liters"]:
                frappe.throw(
                    f"Credit sale liters for <b>{fuel_type}</b> ({credit_data['liters']}) "
                    f"exceed total nozzle dispensed liters ({nozzle_data['liters']}). "
                    "Credit sales cannot be more than what was dispensed."
                )

        # Credit + Card cannot exceed Total Sales (can't collect more than sold)
        total_sales = sum(d["amount"] for d in nozzle_by_fuel.values()) if nozzle_by_fuel else 0
        total_credit = flt(self.credit_amount) or sum(d["amount"] for d in credit_by_fuel.values())
        total_card = flt(self.card_amount)

        if total_sales > 0 and (total_credit + total_card) > total_sales:
            frappe.throw(
                f"Credit Sales + Card/POS ({frappe.format_value(total_credit + total_card, 'Currency')}) "
                f"exceed Total Sales ({frappe.format_value(total_sales, 'Currency')}).<br><br>"
                f"Credit Sales: {frappe.format_value(total_credit, 'Currency')}<br>"
                f"Card/POS: {frappe.format_value(total_card, 'Currency')}<br><br>"
                "Credit and card collections cannot exceed what was sold from nozzles."
            )

    def before_save(self):
        self.calculate_readings()
        self.calculate_credit_totals()
        self.calculate_expense_totals()
        self.calculate_supplier_payment_totals()
        self.calculate_credit_collection_totals()
        self.calculate_card_totals()
        self.calculate_cash_reconciliation()

    def on_submit(self):
        try:
            self.create_stock_entry()
            self.create_sales_invoices()
            self.create_expense_payment_entries()
            self.create_supplier_payment_entries()
            self.create_credit_collection_payment_entries()
            self.update_nozzle_last_readings()
            self.set_approval_status()
        except Exception as e:
            frappe.throw(
                f"<b>Day Closing submit failed while creating transactions.</b><br><br>"
                f"<b>Error:</b> {str(e)}<br><br>"
                f"<b>Details:</b><br>"
                f"Total Sales: {frappe.format_value(self.total_sales, 'Currency')}<br>"
                f"Credit Sales: {frappe.format_value(self.credit_amount, 'Currency')}<br>"
                f"Card/POS: {frappe.format_value(self.card_amount, 'Currency')}<br>"
                f"Expenses: {frappe.format_value(self.total_expenses, 'Currency')}<br>"
                f"Supplier Payments: {frappe.format_value(self.total_supplier_payments, 'Currency')}<br>"
                f"Credit Collections: {frappe.format_value(self.total_credit_collections, 'Currency')}<br>"
                f"Cash Amount: {frappe.format_value(self.cash_amount, 'Currency')}<br>"
                f"Previous Cash: {frappe.format_value(self.previous_cash, 'Currency')}<br>"
                f"Cash in Hand: {frappe.format_value(self.cash_in_hand, 'Currency')}"
            )
    
    def on_cancel(self):
        """Cancel all auto-created transactions when Day Closing is cancelled"""
        self.cancel_linked_transactions()
        self.revert_nozzle_readings()
    
    def set_approval_status(self):
        """Set approval status"""
        self.db_set('workflow_state', 'Approved')

    def get_pump_cost_center(self):
        """Get cost center for this petrol pump, falling back to company default."""
        company = frappe.db.get_value("Petrol Pump", self.petrol_pump, "company")
        cost_center = frappe.db.get_value("Petrol Pump", self.petrol_pump, "cost_center")
        if not cost_center:
            cost_center = frappe.get_cached_value("Company", company, "cost_center")
        return cost_center

    def get_current_rate(self, fuel_type, petrol_pump=None):
        if not fuel_type:
            return 0
        pump = petrol_pump or self.petrol_pump
        if not pump:
            return 0
        rate = frappe.db.sql(
            """
            SELECT fpd.price_per_liter 
            FROM `tabFuel Price Detail` fpd
            JOIN `tabFuel Price` fp ON fpd.parent = fp.name
            WHERE fpd.fuel_type = %s AND fp.petrol_pump = %s AND fp.effective_from <= %s
            ORDER BY fp.effective_from DESC LIMIT 1
            """,
            (fuel_type, pump, now_datetime()),
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

    def calculate_expense_totals(self):
        """Calculate total expenses from expenses child table"""
        total_expenses = 0.0
        for expense in getattr(self, "expenses", []) or []:
            total_expenses += flt(getattr(expense, "amount", 0))
        self.total_expenses = total_expenses

    def calculate_card_totals(self):
        """Calculate total card/POS amount from card_sales child table"""
        total_card = 0.0
        for row in getattr(self, "card_sales", []) or []:
            total_card += flt(getattr(row, "amount", 0))
        self.card_amount = total_card

    def calculate_supplier_payment_totals(self):
        """Calculate total supplier payments from supplier_payments child table"""
        total = 0.0
        for row in getattr(self, "supplier_payments", []) or []:
            total += flt(getattr(row, "amount", 0))
        self.total_supplier_payments = total

    def calculate_credit_collection_totals(self):
        """Calculate total credit collections from credit_collections child table"""
        total = 0.0
        for row in getattr(self, "credit_collections", []) or []:
            total += flt(getattr(row, "amount", 0))
        self.total_credit_collections = total

    def calculate_cash_reconciliation(self):
        """Auto-calculate cash and cash-in-hand.

        Cash Amount = Total Sales - Credit - Card - Expenses - Supplier Payments + Credit Collections
        (net cash received today from all operations)

        Cash in Hand = Previous Cash Balance (GL) + Cash Amount
        (closing cash position at the pump)
        """
        self.cash_amount = (
            flt(self.total_sales)
            - flt(self.credit_amount)
            - flt(self.card_amount)
            - flt(self.total_expenses)
            - flt(self.total_supplier_payments)
            + flt(self.total_credit_collections)
        )

        self.cash_in_hand = flt(self.previous_cash) + flt(self.cash_amount)

    def calculate_credit_totals(self):
        """Aggregate credit liters and amount from credit_details child table.
        
        Also auto-fills rate and calculates amount for each row if not set.

        - Auto-fills rate from active fuel price if fuel_type is set
        - Auto-calculates amount = liters × rate for each row
        - Sums liters and amount across all rows
        - Writes back to credit_sales_liters and credit_amount fields on the parent
        """
        total_liters = 0.0
        total_amount = 0.0

        for d in getattr(self, "credit_details", []) or []:
            # Auto-fill rate if fuel_type is set but rate is missing
            if getattr(d, "fuel_type", None) and not getattr(d, "rate", None):
                rate = self.get_current_rate(getattr(d, "fuel_type"))
                if rate:
                    d.rate = rate
            
            # Auto-calculate amount if liters and rate are available
            liters = flt(getattr(d, "liters", 0))
            rate = flt(getattr(d, "rate", 0))
            if liters > 0 and rate > 0:
                d.amount = liters * rate
            
            total_liters += liters
            total_amount += flt(getattr(d, "amount", 0))

        self.credit_sales_liters = total_liters
        self.credit_amount = total_amount

    def create_stock_entry(self):
        fuel_consumption = {}
        for d in self.nozzle_readings:
            if d.dispensed_liters > 0:
                fuel_consumption[d.fuel_type] = fuel_consumption.get(d.fuel_type, 0) + d.dispensed_liters
        if not fuel_consumption:
            return
        cost_center = self.get_pump_cost_center()
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
                    "cost_center": cost_center,
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

    def create_sales_invoices(self):
        """Create Sales Invoices for cash sales and credit customers separately"""
        if not self.total_sales or self.total_sales <= 0:
            return
        
        # Get company and currency
        company = frappe.db.get_value("Petrol Pump", self.petrol_pump, "company")
        company_currency = frappe.db.get_value("Company", company, "default_currency")
        
        # Get credit sales by customer and fuel type
        credit_sales_by_customer = {}
        total_credit_amount = 0
        for credit_row in getattr(self, "credit_details", []) or []:
            if credit_row.customer and credit_row.liters and credit_row.liters > 0 and credit_row.fuel_type:
                # Create unique key for customer + fuel_type combination
                key = f"{credit_row.customer}::{credit_row.fuel_type}"
                if key not in credit_sales_by_customer:
                    credit_sales_by_customer[key] = {
                        'customer': credit_row.customer,
                        'fuel_type': credit_row.fuel_type,
                        'qty': 0,
                        'rate': credit_row.rate or 0,
                        'amount': 0
                    }
                credit_sales_by_customer[key]['qty'] += flt(credit_row.liters)
                credit_sales_by_customer[key]['amount'] += flt(credit_row.amount)
                total_credit_amount += flt(credit_row.amount)
                # Use rate from credit detail if available
                if credit_row.rate:
                    credit_sales_by_customer[key]['rate'] = credit_row.rate
        
        # Group total sales by fuel type from nozzle readings (includes cash + credit)
        cash_fuel_sales = {}
        cash_sales_amount = 0
        for d in self.nozzle_readings:
            if d.dispensed_liters > 0 and d.fuel_type:
                if d.fuel_type not in cash_fuel_sales:
                    cash_fuel_sales[d.fuel_type] = {
                        'qty': 0,
                        'rate': d.rate,
                        'amount': 0
                    }
                cash_fuel_sales[d.fuel_type]['qty'] += flt(d.dispensed_liters)
                cash_fuel_sales[d.fuel_type]['amount'] += flt(d.amount)
                cash_sales_amount += flt(d.amount)
        
        # Subtract credit sales from cash totals (nozzle readings = cash + credit combined)
        for key, credit_data in credit_sales_by_customer.items():
            fuel_type = credit_data['fuel_type']
            credit_qty = flt(credit_data['qty'])
            credit_amount = flt(credit_data['amount'])
            
            if fuel_type in cash_fuel_sales:
                cash_fuel_sales[fuel_type]['qty'] -= credit_qty
                cash_fuel_sales[fuel_type]['amount'] -= credit_amount
                cash_sales_amount -= credit_amount
        
        created_invoices = []
        cost_center = self.get_pump_cost_center()
        
        # Create Sales Invoice for cash sales
        if cash_sales_amount > 0 and cash_fuel_sales:
            cash_customer = self.get_or_create_cash_customer(company)
            si = frappe.new_doc("Sales Invoice")
            si.customer = cash_customer
            si.company = company
            si.currency = company_currency
            si.cost_center = cost_center
            si.posting_date = self.reading_date or nowdate()
            si.set_posting_time = 1
            si.due_date = self.reading_date or nowdate()
            
            for fuel_type, data in cash_fuel_sales.items():
                if data['qty'] > 0:
                    si.append("items", {
                        "item_code": fuel_type,
                        "qty": data['qty'],
                        "rate": data['rate'],
                        "amount": data['amount'],
                        "uom": "Litre",
                        "cost_center": cost_center,
                    })
            
            if si.items:
                si.insert()
                si.submit()
                created_invoices.append(si.name)
                # Store first cash invoice reference for cancellation handling
                if not self.sales_invoice_ref:
                    self.db_set('sales_invoice_ref', si.name)
                frappe.msgprint(f"Sales Invoice {si.name} created for cash sales: {cash_sales_amount}")
        
        # Create separate Sales Invoice for each credit customer (grouped by customer + fuel_type)
        for key, sales_data in credit_sales_by_customer.items():
            if sales_data['qty'] > 0:
                customer = sales_data['customer']
                fuel_type = sales_data['fuel_type']
                
                if not fuel_type:
                    frappe.throw(f"Fuel type is required for credit customer {customer}. Please set fuel type in credit details.")
                
                si = frappe.new_doc("Sales Invoice")
                si.customer = customer
                si.company = company
                si.currency = company_currency
                si.cost_center = cost_center
                si.posting_date = self.reading_date or nowdate()
                si.set_posting_time = 1
                si.due_date = self.reading_date or nowdate()
                
                si.append("items", {
                    "item_code": fuel_type,
                    "qty": sales_data['qty'],
                    "rate": sales_data['rate'],
                    "amount": sales_data['amount'],
                    "uom": "Litre",
                    "cost_center": cost_center,
                })
                
                si.insert()
                si.submit()
                created_invoices.append(si.name)
                frappe.msgprint(f"Sales Invoice {si.name} created for credit customer {customer} ({fuel_type}): {sales_data['amount']}")
        
        # Store all invoice references (comma-separated for cancellation)
        if created_invoices:
            self.db_set('sales_invoice_ref', ', '.join(created_invoices))
        
        # Create Payment Entries against the cash customer Sales Invoice
        # Cash portion goes to cash account, card portions go to respective bank accounts
        if cash_sales_amount > 0 and created_invoices:
            cash_invoice_name = created_invoices[0]
            cash_invoice_doc = frappe.get_doc("Sales Invoice", cash_invoice_name)
            self.create_collection_payment_entries(cash_invoice_doc, company)
    
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
    
    def create_collection_payment_entries(self, sales_invoice, company):
        """Create Payment Entries for cash and card collections against the Cash SI.

        Strategy: use the SI's actual outstanding as the truth.
        1. Card PEs are created first (exact amounts per bank).
        2. Cash PE gets whatever outstanding remains on the SI.
        This avoids rounding mismatches between our totals and the SI grand_total.
        """
        company_currency = frappe.db.get_value("Company", company, "default_currency")
        default_receivable_account = frappe.get_cached_value("Company", company, "default_receivable_account")

        created_pe_names = []

        # --- 1. Card/POS Payment Entries first (exact amounts per bank) ---
        card_by_bank = {}
        for row in getattr(self, "card_sales", []) or []:
            if not row.bank_account or flt(row.amount) <= 0:
                continue
            if row.bank_account not in card_by_bank:
                card_by_bank[row.bank_account] = 0
            card_by_bank[row.bank_account] += flt(row.amount)

        for bank_account_name, card_amount in card_by_bank.items():
            if card_amount <= 0:
                continue

            outstanding = self._get_si_outstanding(sales_invoice.name)
            if outstanding <= 0:
                break

            gl_account = frappe.db.get_value("Bank Account", bank_account_name, "account")
            if not gl_account:
                frappe.throw(
                    f"Bank Account '<b>{bank_account_name}</b>' does not have a linked GL Account. "
                    "Please set the Account field on the Bank Account document."
                )

            mode_of_payment = frappe.db.get_value(
                "Mode of Payment", {"type": "Bank"}, "name"
            ) or "Bank Draft"

            allocate = min(flt(card_amount), outstanding)
            pe = self._make_payment_entry(
                sales_invoice_name=sales_invoice.name,
                customer=sales_invoice.customer,
                grand_total=flt(sales_invoice.grand_total),
                company=company,
                currency=company_currency,
                paid_from=default_receivable_account,
                paid_to=gl_account,
                amount=allocate,
                mode_of_payment=mode_of_payment,
            )
            if pe:
                created_pe_names.append(pe.name)
                bank_label = frappe.db.get_value("Bank Account", bank_account_name, "bank") or bank_account_name
                frappe.msgprint(f"Payment Entry {pe.name} created for card ({bank_label}): {allocate}")

        # --- 2. Cash PE gets whatever is left on the SI ---
        outstanding = self._get_si_outstanding(sales_invoice.name)
        if outstanding > 0:
            mode_of_payment = frappe.db.get_value("Mode of Payment", {"type": "Cash"}, "name") or "Cash"
            cash_account = frappe.db.get_value(
                "Mode of Payment Account",
                {"parent": mode_of_payment, "company": company},
                "default_account"
            )
            if not cash_account:
                cash_account = frappe.get_cached_value("Company", company, "default_cash_account")

            pe = self._make_payment_entry(
                sales_invoice_name=sales_invoice.name,
                customer=sales_invoice.customer,
                grand_total=flt(sales_invoice.grand_total),
                company=company,
                currency=company_currency,
                paid_from=default_receivable_account,
                paid_to=cash_account,
                amount=outstanding,
                mode_of_payment=mode_of_payment,
            )
            if pe:
                created_pe_names.append(pe.name)
                frappe.msgprint(f"Payment Entry {pe.name} created for cash: {outstanding}")

        if created_pe_names:
            self.db_set('payment_entry_ref', ', '.join(created_pe_names))

    def _get_si_outstanding(self, si_name):
        """Get fresh outstanding amount from DB."""
        return flt(frappe.db.get_value("Sales Invoice", si_name, "outstanding_amount"))

    def _make_payment_entry(self, sales_invoice_name, customer, grand_total,
                            company, currency, paid_from, paid_to, amount,
                            mode_of_payment):
        """Create and submit a single Payment Entry."""
        outstanding = self._get_si_outstanding(sales_invoice_name)
        allocate = min(flt(amount), outstanding)

        if allocate <= 0:
            return None

        pe = frappe.new_doc("Payment Entry")
        pe.payment_type = "Receive"
        pe.party_type = "Customer"
        pe.party = customer
        pe.company = company
        pe.cost_center = self.get_pump_cost_center()
        pe.posting_date = self.reading_date or nowdate()

        pe.paid_from_account_currency = currency
        pe.paid_to_account_currency = currency
        pe.source_exchange_rate = 1.0
        pe.target_exchange_rate = 1.0

        pe.paid_from = paid_from
        pe.paid_to = paid_to

        pe.paid_amount = flt(allocate)
        pe.received_amount = flt(allocate)
        pe.mode_of_payment = mode_of_payment
        pe.reference_no = self.name
        pe.reference_date = self.reading_date or nowdate()

        pe.append("references", {
            "reference_doctype": "Sales Invoice",
            "reference_name": sales_invoice_name,
            "total_amount": flt(grand_total),
            "outstanding_amount": outstanding,
            "allocated_amount": flt(allocate),
        })

        pe.insert()
        pe.submit()
        return pe

    def create_expense_payment_entries(self):
        """Create Journal Entries for expenses - debits expense accounts and credits cash account"""
        if not getattr(self, "expenses", None) or not self.expenses:
            return
        
        company = frappe.db.get_value("Petrol Pump", self.petrol_pump, "company")
        if not company:
            return
        
        # Get company's default currency
        company_currency = frappe.db.get_value("Company", company, "default_currency")
        
        # Get cash account from mode of payment or company default
        mode_of_payment = frappe.db.get_value("Mode of Payment", {"type": "Cash"}, "name") or "Cash"
        cash_account = frappe.db.get_value(
            "Mode of Payment Account",
            {"parent": mode_of_payment, "company": company},
            "default_account"
        )
        if not cash_account:
            cash_account = frappe.get_cached_value("Company", company, "default_cash_account")
        
        if not cash_account:
            frappe.throw("Cash account not found. Please configure Mode of Payment or Company default cash account.")
        
        # Get pump-specific cost center for location-wise reporting
        cost_center = self.get_pump_cost_center()
        
        created_journal_entries = []
        
        # Group expenses by expense account to create fewer journal entries
        expenses_by_account = {}
        for expense in self.expenses:
            if not expense.expense_account or not expense.amount or flt(expense.amount) <= 0:
                continue
            
            # Verify expense account exists and is an expense account
            account_type = frappe.db.get_value("Account", expense.expense_account, "account_type")
            if account_type not in ["Expense", "Expenses Included In Valuation", "Expenses Included In Asset Valuation"]:
                frappe.msgprint(
                    f"Warning: Account {expense.expense_account} is not an expense account type. Proceeding anyway.",
                    indicator="orange"
                )
            
            if expense.expense_account not in expenses_by_account:
                expenses_by_account[expense.expense_account] = []
            expenses_by_account[expense.expense_account].append(expense)
        
        # Create one Journal Entry per expense account (or combine all if preferred)
        for expense_account, expense_list in expenses_by_account.items():
            total_amount = sum(flt(exp.amount) for exp in expense_list)
            
            # Create Journal Entry for expenses
            je = frappe.new_doc("Journal Entry")
            je.voucher_type = "Cash Entry"  # Since it's from cash account
            je.company = company
            je.posting_date = self.reading_date or nowdate()
            je.set_posting_time = 1
            je.user_remark = f"Expenses from Day Closing {self.name}"
            
            # Debit: Expense Account
            je.append("accounts", {
                "account": expense_account,
                "debit_in_account_currency": total_amount,
                "cost_center": cost_center,
                "account_currency": company_currency,
                "exchange_rate": 1.0
            })
            
            # Credit: Cash Account
            je.append("accounts", {
                "account": cash_account,
                "credit_in_account_currency": total_amount,
                "cost_center": cost_center,
                "account_currency": company_currency,
                "exchange_rate": 1.0
            })
            
            # Add reference to Day Closing
            je.cheque_no = self.name
            je.cheque_date = self.reading_date or nowdate()
            
            je.insert(ignore_permissions=True)
            je.submit()
            created_journal_entries.append(je.name)
            
            # Build description for message
            expense_descriptions = [f"{exp.description or 'Expense'} ({flt(exp.amount)})" for exp in expense_list]
            desc_text = ", ".join(expense_descriptions)
            frappe.msgprint(f"Journal Entry {je.name} created for expenses: {expense_account} - {total_amount} ({desc_text})")
        
        # Store journal entry references (comma-separated)
        if created_journal_entries:
            self.db_set('expense_payment_entries_ref', ', '.join(created_journal_entries))

    def create_supplier_payment_entries(self):
        """Create Payment Entries (Pay type) for each supplier payment row.

        Debits the supplier's default payable account and credits the cash account.
        """
        if not getattr(self, "supplier_payments", None) or not self.supplier_payments:
            return

        company = frappe.db.get_value("Petrol Pump", self.petrol_pump, "company")
        if not company:
            return

        company_currency = frappe.db.get_value("Company", company, "default_currency")
        default_payable_account = frappe.get_cached_value("Company", company, "default_payable_account")

        # Get cash account
        mode_of_payment = frappe.db.get_value("Mode of Payment", {"type": "Cash"}, "name") or "Cash"
        cash_account = frappe.db.get_value(
            "Mode of Payment Account",
            {"parent": mode_of_payment, "company": company},
            "default_account"
        )
        if not cash_account:
            cash_account = frappe.get_cached_value("Company", company, "default_cash_account")

        if not cash_account:
            frappe.throw("Cash account not found. Please configure Mode of Payment or Company default cash account.")

        cost_center = self.get_pump_cost_center()
        created_pe_names = []

        for row in self.supplier_payments:
            if not row.supplier or flt(row.amount) <= 0:
                continue

            pe = frappe.new_doc("Payment Entry")
            pe.payment_type = "Pay"
            pe.party_type = "Supplier"
            pe.party = row.supplier
            pe.company = company
            pe.cost_center = cost_center
            pe.posting_date = self.reading_date or nowdate()

            pe.paid_from = cash_account
            pe.paid_to = default_payable_account
            pe.paid_from_account_currency = company_currency
            pe.paid_to_account_currency = company_currency
            pe.source_exchange_rate = 1.0
            pe.target_exchange_rate = 1.0

            pe.paid_amount = flt(row.amount)
            pe.received_amount = flt(row.amount)
            pe.mode_of_payment = mode_of_payment
            pe.reference_no = self.name
            pe.reference_date = self.reading_date or nowdate()

            pe.insert(ignore_permissions=True)
            pe.submit()
            created_pe_names.append(pe.name)

            ref_text = f" ({row.reference})" if row.reference else ""
            frappe.msgprint(
                f"Payment Entry {pe.name} created for supplier {row.supplier}: {flt(row.amount)}{ref_text}"
            )

        if created_pe_names:
            self.db_set('supplier_payment_entries_ref', ', '.join(created_pe_names))

    def create_credit_collection_payment_entries(self):
        """Create Payment Entries (Receive) for each credit collection row.

        When a credit customer pays back old dues, we receive cash:
        Debit Cash, Credit Receivable (reduces customer outstanding).
        """
        if not getattr(self, "credit_collections", None) or not self.credit_collections:
            return

        company = frappe.db.get_value("Petrol Pump", self.petrol_pump, "company")
        if not company:
            return

        company_currency = frappe.db.get_value("Company", company, "default_currency")
        default_receivable_account = frappe.get_cached_value("Company", company, "default_receivable_account")

        mode_of_payment = frappe.db.get_value("Mode of Payment", {"type": "Cash"}, "name") or "Cash"
        cash_account = frappe.db.get_value(
            "Mode of Payment Account",
            {"parent": mode_of_payment, "company": company},
            "default_account"
        )
        if not cash_account:
            cash_account = frappe.get_cached_value("Company", company, "default_cash_account")

        if not cash_account:
            frappe.throw("Cash account not found. Please configure Mode of Payment or Company default cash account.")

        cost_center = self.get_pump_cost_center()
        created_pe_names = []

        for row in self.credit_collections:
            if not row.customer or flt(row.amount) <= 0:
                continue

            pe = frappe.new_doc("Payment Entry")
            pe.payment_type = "Receive"
            pe.party_type = "Customer"
            pe.party = row.customer
            pe.company = company
            pe.cost_center = cost_center
            pe.posting_date = self.reading_date or nowdate()

            pe.paid_from = default_receivable_account
            pe.paid_to = cash_account
            pe.paid_from_account_currency = company_currency
            pe.paid_to_account_currency = company_currency
            pe.source_exchange_rate = 1.0
            pe.target_exchange_rate = 1.0

            pe.paid_amount = flt(row.amount)
            pe.received_amount = flt(row.amount)
            pe.mode_of_payment = mode_of_payment
            pe.reference_no = self.name
            pe.reference_date = self.reading_date or nowdate()

            pe.insert(ignore_permissions=True)
            pe.submit()
            created_pe_names.append(pe.name)

            desc_text = f" ({row.description})" if row.description else ""
            frappe.msgprint(
                f"Payment Entry {pe.name} created for credit collection from {row.customer}: {flt(row.amount)}{desc_text}"
            )

        if created_pe_names:
            self.db_set('credit_collection_entries_ref', ', '.join(created_pe_names))

    def update_nozzle_last_readings(self):
        """Update last_reading on Nozzle master when Day Closing is submitted.

        Mirrors the behaviour in Shift Reading:
        - Match by (petrol_pump, nozzle_name)
        - Write current_reading into Nozzle.last_reading
        """
        for nozzle_reading in self.nozzle_readings or []:
            nozzle_name = getattr(nozzle_reading, "nozzle_number", None)
            if not nozzle_name:
                continue

            nozzle_docname = frappe.db.get_value(
                "Nozzle",
                {"petrol_pump": self.petrol_pump, "nozzle_name": nozzle_name},
                "name",
            )
            if nozzle_docname:
                frappe.db.set_value(
                    "Nozzle",
                    nozzle_docname,
                    "last_reading",
                    flt(getattr(nozzle_reading, "current_reading", 0)),
                )
    
    def revert_nozzle_readings(self):
        """Revert nozzle readings on Nozzle master when Day Closing is cancelled."""
        for nozzle_reading in self.nozzle_readings or []:
            nozzle_name = getattr(nozzle_reading, "nozzle_number", None)
            if not nozzle_name:
                continue

            nozzle_docname = frappe.db.get_value(
                "Nozzle",
                {"petrol_pump": self.petrol_pump, "nozzle_name": nozzle_name},
                "name",
            )
            if nozzle_docname:
                frappe.db.set_value(
                    "Nozzle",
                    nozzle_docname,
                    "last_reading",
                    flt(getattr(nozzle_reading, "previous_reading", 0)),
                )
        frappe.msgprint("Nozzle readings reverted to previous values")
    
    def cancel_linked_transactions(self):
        """Cancel all auto-created transactions (Stock Entry, Sales Invoice, Payment Entry, Expense Payment Entries)"""
        errors = []
        
        # Cancel Credit Collection Payment Entries first
        if getattr(self, "credit_collection_entries_ref", None):
            cc_refs = [ref.strip() for ref in str(self.credit_collection_entries_ref).split(',')]
            for cc_ref in cc_refs:
                try:
                    pe = frappe.get_doc("Payment Entry", cc_ref)
                    if pe.docstatus == 1:
                        pe.cancel()
                        frappe.msgprint(f"Credit Collection Payment Entry {cc_ref} cancelled")
                except Exception as e:
                    errors.append(f"Credit Collection Payment Entry {cc_ref}: {str(e)}")

        # Cancel Supplier Payment Entries
        if getattr(self, "supplier_payment_entries_ref", None):
            supplier_refs = [ref.strip() for ref in str(self.supplier_payment_entries_ref).split(',')]
            for supplier_ref in supplier_refs:
                try:
                    pe = frappe.get_doc("Payment Entry", supplier_ref)
                    if pe.docstatus == 1:
                        pe.cancel()
                        frappe.msgprint(f"Supplier Payment Entry {supplier_ref} cancelled")
                except Exception as e:
                    errors.append(f"Supplier Payment Entry {supplier_ref}: {str(e)}")

        # Cancel Expense Journal Entries (must be done before main payment entry)
        if getattr(self, "expense_payment_entries_ref", None):
            expense_refs = [ref.strip() for ref in str(self.expense_payment_entries_ref).split(',')]
            for expense_ref in expense_refs:
                try:
                    je = frappe.get_doc("Journal Entry", expense_ref)
                    if je.docstatus == 1:  # Only cancel if submitted
                        je.cancel()
                        frappe.msgprint(f"Expense Journal Entry {expense_ref} cancelled")
                except Exception as e:
                    errors.append(f"Expense Journal Entry {expense_ref}: {str(e)}")
        
        # Cancel Payment Entries (cash + card collections) - must be done before Sales Invoice
        if self.payment_entry_ref:
            pe_refs = [ref.strip() for ref in str(self.payment_entry_ref).split(',')]
            for pe_ref in pe_refs:
                try:
                    pe = frappe.get_doc("Payment Entry", pe_ref)
                    if pe.docstatus == 1:  # Only cancel if submitted
                        pe.cancel()
                        frappe.msgprint(f"Payment Entry {pe_ref} cancelled")
                except Exception as e:
                    errors.append(f"Payment Entry {pe_ref}: {str(e)}")
        
        # Cancel all Sales Invoices (may be multiple for credit customers)
        if self.sales_invoice_ref:
            invoice_refs = [ref.strip() for ref in str(self.sales_invoice_ref).split(',')]
            for invoice_ref in invoice_refs:
                try:
                    si = frappe.get_doc("Sales Invoice", invoice_ref)
                    if si.docstatus == 1:  # Only cancel if submitted
                        si.cancel()
                        frappe.msgprint(f"Sales Invoice {invoice_ref} cancelled")
                except Exception as e:
                    errors.append(f"Sales Invoice {invoice_ref}: {str(e)}")
        
        # Cancel Stock Entry
        if self.stock_entry_ref:
            try:
                se = frappe.get_doc("Stock Entry", self.stock_entry_ref)
                if se.docstatus == 1:  # Only cancel if submitted
                    se.cancel()
                    frappe.msgprint(f"Stock Entry {self.stock_entry_ref} cancelled")
            except Exception as e:
                errors.append(f"Stock Entry {self.stock_entry_ref}: {str(e)}")
        
        # Clear all reference fields so amended doc doesn't link to cancelled documents
        self.db_set('stock_entry_ref', None)
        self.db_set('sales_invoice_ref', None)
        self.db_set('payment_entry_ref', None)
        self.db_set('expense_payment_entries_ref', None)
        self.db_set('supplier_payment_entries_ref', None)
        self.db_set('credit_collection_entries_ref', None)

        if errors:
            frappe.msgprint(
                f"Some transactions could not be cancelled:<br>" + "<br>".join(errors),
                indicator="orange",
                alert=True
            )
        else:
            frappe.msgprint("All linked transactions cancelled successfully", indicator="green")

@frappe.whitelist()
def get_current_fuel_rate(fuel_type: str, petrol_pump: str = None, reading_date: str = None):
    """Get current active fuel price rate for a fuel type at a specific petrol pump"""
    if not fuel_type or not petrol_pump:
        return 0
    
    from frappe.utils import now_datetime, getdate
    if reading_date:
        effective_date = getdate(reading_date)
    else:
        effective_date = now_datetime()
    
    rate = frappe.db.sql(
        """
        SELECT fpd.price_per_liter 
        FROM `tabFuel Price Detail` fpd
        JOIN `tabFuel Price` fp ON fpd.parent = fp.name
        WHERE fpd.fuel_type = %s AND fp.petrol_pump = %s AND fp.effective_from <= %s
        ORDER BY fp.effective_from DESC LIMIT 1
        """,
        (fuel_type, petrol_pump, effective_date),
    )
    return rate[0][0] if rate and rate[0] else 0

@frappe.whitelist()
def get_active_nozzles_for_day_closing(petrol_pump: str, reading_date: str = None):
    """Get active nozzles with previous reading from last Day Closing or Nozzle.last_reading"""
    rows = []
    if not petrol_pump:
        return rows
    
    from frappe.utils import getdate, nowdate
    if reading_date:
        reading_date_obj = getdate(reading_date)
    else:
        reading_date_obj = getdate(nowdate())
    
    # Get all active nozzles
    nozzles = frappe.get_all(
        "Nozzle",
        filters={"petrol_pump": petrol_pump, "is_active": 1},
        fields=["name", "nozzle_name", "fuel_type", "last_reading", "opening_reading"],
    )
    
    for n in nozzles:
        # Try to get previous reading from last submitted Day Closing
        previous_reading = None
        
        # Get the last submitted Day Closing for this pump on or before the reading date
        last_day_closing = frappe.db.sql("""
            SELECT name 
            FROM `tabDay Closing`
            WHERE petrol_pump = %s 
            AND docstatus = 1 
            AND reading_date <= %s
            ORDER BY reading_date DESC, creation DESC
            LIMIT 1
        """, (petrol_pump, reading_date_obj), as_dict=True)
        
        if last_day_closing:
            # Get the current_reading for this nozzle from the last Day Closing
            nozzle_reading = frappe.db.sql("""
                SELECT current_reading
                FROM `tabNozzle Reading Detail`
                WHERE parent = %s 
                AND nozzle_number = %s
                LIMIT 1
            """, (last_day_closing[0].name, n.nozzle_name), as_dict=True)
            
            if nozzle_reading and nozzle_reading[0].current_reading is not None:
                previous_reading = flt(nozzle_reading[0].current_reading)
        
        # Fallback to Nozzle.last_reading or opening_reading
        if previous_reading is None:
            previous_reading = n.last_reading or n.opening_reading or 0
        
        rows.append({
            "nozzle_number": n.nozzle_name,
            "fuel_type": n.fuel_type,
            "previous_reading": previous_reading,
            "current_reading": 0,
            "rate": DayClosing.get_current_rate(DayClosing, n.fuel_type, petrol_pump),
        })
    
    return rows

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


@frappe.whitelist()
@frappe.validate_and_sanitize_search_inputs
def get_indirect_expense_accounts(doctype, txt, searchfield, start, page_len, filters):
    """
    Get accounts that are under 'Indirect Expenses' parent account.
    This method is used as a query filter for expense_account field.
    """
    # Build search condition for text search
    search_condition = ""
    if txt:
        search_condition = f"AND (acc.name LIKE %(txt)s OR acc.account_name LIKE %(txt)s)"
    
    # Query to get all accounts that have 'Indirect Expenses' in their parent hierarchy
    # This uses a recursive approach to find all descendants of accounts containing 'Indirect Expenses'
    accounts = frappe.db.sql("""
        SELECT acc.name, acc.account_name
        FROM `tabAccount` acc
        WHERE acc.is_group = 0
        AND acc.root_type = 'Expense'
        AND (
            acc.parent_account LIKE '%%Indirect Expense%%'
            OR acc.name LIKE '%%Indirect Expense%%'
            OR EXISTS (
                SELECT 1 FROM `tabAccount` parent
                WHERE parent.name = acc.parent_account
                AND (
                    parent.parent_account LIKE '%%Indirect Expense%%'
                    OR parent.name LIKE '%%Indirect Expense%%'
                )
            )
        )
        {search_condition}
        ORDER BY acc.name
        LIMIT %(start)s, %(page_len)s
    """.format(search_condition=search_condition), {
        "txt": f"%{txt}%",
        "start": start,
        "page_len": page_len
    }, as_list=True)
    
    return accounts


@frappe.whitelist()
def get_previous_cash(petrol_pump: str, reading_date: str = None):
    """Get Cash In Hand GL balance for this pump's cost center.

    Pulls the actual accounting balance of the cash account filtered by
    the petrol pump's cost center, giving the real cash position.
    """
    if not petrol_pump:
        return 0

    from frappe.utils import getdate, nowdate
    if reading_date:
        reading_date_obj = getdate(reading_date)
    else:
        reading_date_obj = getdate(nowdate())

    company = frappe.db.get_value("Petrol Pump", petrol_pump, "company")
    if not company:
        return 0

    # Get the cash account
    mode_of_payment = frappe.db.get_value("Mode of Payment", {"type": "Cash"}, "name") or "Cash"
    cash_account = frappe.db.get_value(
        "Mode of Payment Account",
        {"parent": mode_of_payment, "company": company},
        "default_account"
    )
    if not cash_account:
        cash_account = frappe.get_cached_value("Company", company, "default_cash_account")

    if not cash_account:
        return 0

    # Get the pump's cost center
    cost_center = frappe.db.get_value("Petrol Pump", petrol_pump, "cost_center")

    # Build GL query — sum of (debit - credit) up to the reading date
    conditions = "gle.account = %s AND gle.company = %s AND gle.is_cancelled = 0 AND gle.posting_date < %s"
    params = [cash_account, company, reading_date_obj]

    if cost_center:
        conditions += " AND gle.cost_center = %s"
        params.append(cost_center)

    balance = frappe.db.sql("""
        SELECT COALESCE(SUM(gle.debit - gle.credit), 0) as balance
        FROM `tabGL Entry` gle
        WHERE {conditions}
    """.format(conditions=conditions), params)

    return flt(balance[0][0]) if balance else 0
