## Petrol Pump V2 - CFO Blueprint

This document defines an end-to-end, finance-grade operating model for Petrol Pump V2 across masters, inventory, pricing, revenue recognition, controls, and reporting.

### 1) Master Data Backbone
- Fuel Types = Items (auto-created)
  - Item Code = Fuel Type name; Stock UOM = Litre; Is Stock Item = true.
  - Optional: set default income/expense accounts and tax templates.
- Fuel Tank = Warehouse
  - Each tank links to a dedicated Warehouse and a single Fuel Type.
- Dispenser & Nozzles
  - Each nozzle links to a tank (child rows under Dispenser).
  - Maintain `last_reading` per nozzle.

### 2) Inventory Integrity
- Opening stock
  - Stock Entry (Material Receipt) to each tank’s warehouse for its Fuel Type Item (with basic_rate for valuation).
- Daily consumption
  - Day Closing submits a Stock Entry (Material Issue) by fuel type from tank warehouses (already implemented).
  - Validation blocks zero/negative remaining stock (implemented).
- Transfers
  - Fuel Transfer submits Material Transfer from source tank warehouse to destination tank warehouse.
- Reconciliation
  - Dip Reading records measured stock vs system stock. Variance workflow to approve and auto-post Stock Reconciliation (recommended enhancement).

### 3) Pricing & Revenue Recognition
- Fuel Price governance
  - Effective-dated, active prices. Block submit if no effective price for any line (recommended enforcement).
- Options to recognize revenue (choose one):
  - A) Sales Invoice on Day Closing submit
    - One invoice per fuel type or consolidated to “Cash Customer”; auto Payment Entry for cash; link posting time to Material Issue.
  - B) POS/Ticket-based
    - Accumulate tickets; Day Closing consolidates and creates Sales Invoice; Material Issue remains source of CoGS.
  - C) Journal-based daily revenue
    - Day Closing creates Journal Entry: Dr Cash/Bank/AR, Cr Sales (no customer detail). CoGS from Material Issue.

### 4) Controls & Approvals
- Roles
  - Operator: prepare Day Closing; cannot submit with variance or missing price.
  - Supervisor: approves variance and submits.
  - Accountant: reviews revenue & cash reconciliation; posts bank deposits.
- Hard stops (recommended)
  - No submit if price missing/zero on any line.
  - No submit if remaining stock ≤ 0 (implemented).
  - Comment & attachment required for price override or large variances.

### 5) Cash & Credit Handling
- Cash
  - Capture per Day Closing (add Cash Reconciliation child table with denominations/UPI/terminal totals). Must reconcile to invoice receipts.
- Credit customers
  - Option 1: Simple total liters on credit (present field exists).
  - Option 2: Customer-wise child rows (customer, liters, rate, amount) and auto-generate Sales Invoices.

### 6) Reporting Pack
- Day Closing Summary: liters, revenue, variance, prices, by pump/date.
- Nozzle Performance: liters per nozzle; abnormal spikes/drops.
- Tank Reconciliation: opening + receipts − issues − transfers − losses = closing.
- Margin Report: Sales vs CoGS by day/pump/fuel type.
- Price History: effective-from log; user; reason.

### 7) Data Hygiene & Migration
- Ensure Items exist for all Fuel Types (auto-created on save; backfill by opening each Fuel Type).
- Ensure each Fuel Tank has a Warehouse and opening stock posted to that warehouse for its Fuel Type Item.
- Lock past Day Closings after submit; changes via amendment only.
- Series prefixes are controlled; reset only in test/dev (done for current prefixes).

### 8) Near-Term Enhancements (Recommended)
1. Day Closing → Sales Invoice (Option A)
   - Create consolidated invoice to “Cash Customer”; auto Payment Entry; align posting with Material Issue.
2. Dip variance workflow
   - Compute expected closing; if variance beyond tolerance, require Supervisor approval; auto Stock Reconciliation.
3. Cash Reconciliation child table
   - Denomination counts, UPI slips, terminal totals; must match invoice receipts.
4. Customer credit capture (optional)
   - Customer-wise child rows; auto-generate Sales Invoices for those rows.

### 9) Operational Checklists
- Day start
  - Confirm price changes effective (Fuel Price).
  - Confirm tank stock available (Stock Balance by tank warehouses).
- Day close
  - Auto-populate nozzles; enter current readings.
  - Review totals; ensure no price gaps.
  - Submit Day Closing (creates Material Issue; optionally Sales Invoice).
  - Review cash reconciliation; post bank deposit.

### 10) KPIs
- Gross margin per fuel type, per day, per pump.
- Liters variance (dip vs system) and trend.
- Price change impact on margin.
- Cash over/short.

---

If you approve this blueprint, I can implement:
- (A) Sales Invoice + Payment Entry on Day Closing submit
- Dip variance workflow + auto Stock Reconciliation
- Cash Reconciliation child table + report
- Customer credit child + auto invoicing
