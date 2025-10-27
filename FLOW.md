# 🔄 Petrol Pump V2 - Complete System Flow

This document provides a comprehensive step-by-step guide to using the Petrol Pump Management System, including what happens behind the scenes and what to verify at each step.

---

## 📖 Table of Contents

1. [System Overview](#system-overview)
2. [Phase 1: Master Data Setup](#phase-1-master-data-setup)
3. [Phase 2: Initial Stock Receipt](#phase-2-initial-stock-receipt)
4. [Phase 3: Daily Operations](#phase-3-daily-operations)
5. [Phase 4: Shift-Based Operations](#phase-4-shift-based-operations)
6. [Phase 5: Quality Control](#phase-5-quality-control)
7. [Phase 6: Fuel Transfers](#phase-6-fuel-transfers)
8. [Phase 7: Corrections & Cancellations](#phase-7-corrections--cancellations)
9. [Phase 8: Reports & Reconciliation](#phase-8-reports--reconciliation)
10. [Critical Cross-Checks](#critical-cross-checks)

---

## System Overview

### Business Model

**One Accountant Per Branch**
- Each petrol pump has one accountant who enters all data
- Workers (pump attendants) do not have system access
- Workers collect:
  - Nozzle meter readings
  - Cash and card slips
  - Customer information for credit sales
- At day end, workers give all data to accountant
- Accountant enters everything into the system

### Data Flow Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                         PHYSICAL WORLD                           │
└─────────────────────────────────────────────────────────────────┘
                              │
                    ┌─────────┴──────────┐
                    │                    │
              ┌─────▼─────┐      ┌──────▼──────┐
              │  WORKERS  │      │ ACCOUNTANT  │
              │ (No Access)│      │ (Full Access)│
              └─────┬─────┘      └──────┬──────┘
                    │                    │
         Collect:   │                    │  Enters:
         • Readings │                    │  • Day Closing
         • Cash     │                    │  • Dip Reading
         • Slips    │                    │  • Fuel Testing
                    │                    │  • Transfers
                    └────────►───────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                    PETROL PUMP V2 SYSTEM                         │
│                                                                  │
│  ┌──────────────┐     ┌──────────────┐     ┌──────────────┐   │
│  │ Day Closing  │────▶│ Stock Entry  │     │ Fuel Tank    │   │
│  │ (Accountant) │     │  (Auto)      │────▶│ (Updated)    │   │
│  └──────────────┘     └──────────────┘     └──────────────┘   │
│         │                                                       │
│         ├────▶ Sales Invoice (Auto)                           │
│         │                                                       │
│         └────▶ Payment Entry (Auto)                           │
│                                                                  │
└──────────────────────────────┬───────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                        ERPNEXT CORE                              │
│                                                                  │
│  Stock Module         Accounts Module        Reports            │
│  • Stock Ledger       • General Ledger       • P&L              │
│  • Stock Balance      • Cash Book            • Balance Sheet    │
│  • Valuation          • Debtors/Creditors    • Stock Analytics  │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

---

## Phase 1: Master Data Setup

### Step 1: Company Setup (ERPNext)

**Location:** `Setup → Company`

**Action:**
1. Create your company (if not exists)
2. Set default currency (e.g., PKR, USD, etc.)
3. Configure default accounts:
   - Cash Account
   - Default Receivable Account
   - Default Payable Account
   - Cost of Goods Sold Account

**What Happens:**
- ERPNext creates company master
- Chart of Accounts generated
- Default fiscal year set

**Cross-Check:**
```
✓ Company created with correct name
✓ Default currency set (e.g., PKR)
✓ Chart of Accounts exists
✓ Fiscal year configured
```

---

### Step 2: Create Fuel Items (ERPNext)

**Location:** `Stock → Item → New`

**Action:**
Create an Item for each fuel type you sell:

```yaml
Item 1:
  Item Code: PETROL-REGULAR
  Item Name: Petrol Regular
  Item Group: Fuel (create group first)
  Stock UOM: Litre
  Default Unit of Measure: Litre
  Valuation Method: FIFO (or Moving Average)
  Maintain Stock: ✓ Yes
  Is Stock Item: ✓ Yes
  Allow Negative Stock: ☐ No
  
Item 2:
  Item Code: DIESEL
  Item Name: Diesel
  Item Group: Fuel
  Stock UOM: Litre
  ...
  
Item 3:
  Item Code: PREMIUM-PETROL
  Item Name: Premium Petrol
  ...
```

**What Happens:**
- ERPNext creates item master records
- Stock tracking enabled for each item
- Valuation method set for COGS calculation

**Cross-Check:**
```
✓ Each fuel type has a corresponding Item
✓ Items marked as "Maintain Stock"
✓ Stock UOM = Litre
✓ Valuation Method selected
✓ Items appear in Item List
```

---

### Step 3: Create Warehouses (ERPNext)

**Location:** `Stock → Warehouse → New`

**Action:**
Create warehouses for each pump location:

```yaml
Warehouse 1:
  Warehouse Name: Main Pump - Storage
  Warehouse Type: Transit (or default)
  Parent Warehouse: (optional)
  Company: Your Company
  Is Group: ☐ No

Warehouse 2:
  Warehouse Name: Branch A - Storage
  ...
```

**What Happens:**
- ERPNext creates warehouse locations
- Stock will be tracked separately for each warehouse
- Enables multi-location inventory

**Cross-Check:**
```
✓ Warehouse created for each pump
✓ Linked to correct company
✓ Warehouse is active
```

---

### Step 4: Create Petrol Pump

**Location:** `Petrol Pump V2 → Petrol Pump → New`

**Action:**
```yaml
Petrol Pump:
  Petrol Pump Name: Main Pump Station
  Company: Your Company (link)
  Address: Street, City, Country
  Contact Number: +92-XXX-XXXXXXX
  Manager Name: (optional)
  Email: (optional)
```

**What Happens:**
- Creates pump location master
- Links to company for accounting
- This will be used to filter all data

**Cross-Check:**
```
✓ Petrol Pump created
✓ Company link is correct
✓ Can be selected in other doctypes
```

---

### Step 5: Create Fuel Types

**Location:** `Petrol Pump V2 → Fuel Type → New`

**Action:**
```yaml
Fuel Type 1:
  Naming Series: FUEL-TYPE-
  Fuel Type Name: Petrol Regular
  Description: Regular unleaded petrol

Fuel Type 2:
  Naming Series: FUEL-TYPE-
  Fuel Type Name: Diesel
  Description: High-speed diesel
```

**What Happens:**
- Creates fuel category master
- Auto-naming: FUEL-TYPE-00001, FUEL-TYPE-00002
- Used for price management and reporting

**Cross-Check:**
```
✓ Fuel types created with unique names
✓ Naming series working (FUEL-TYPE-XXXXX)
✓ Fuel types appear in dropdown lists
```

---

### Step 6: Create Fuel Tanks

**Location:** `Petrol Pump V2 → Fuel Tank → New`

**Action:**
```yaml
Tank 1:
  Naming Series: TANK-
  Tank Name: Tank 1 - Petrol Regular
  Petrol Pump: Main Pump Station (link)
  Fuel Type: PETROL-REGULAR (link to ERPNext Item)
  Warehouse: Main Pump - Storage (link to ERPNext Warehouse)
  Capacity (Liters): 10000
  Current Stock: 0 (will auto-update)
  Status: Active

Tank 2:
  Naming Series: TANK-
  Tank Name: Tank 2 - Diesel
  Petrol Pump: Main Pump Station
  Fuel Type: DIESEL
  Warehouse: Main Pump - Storage
  Capacity (Liters): 15000
  ...
```

**What Happens:**
- Links physical underground tank to ERPNext warehouse
- Sets capacity limits
- Enables stock tracking per tank
- Auto-naming: TANK-00001, TANK-00002

**Backend Integration:**
```python
# On save, validates:
- Warehouse belongs to same company as Petrol Pump
- Fuel Type (Item) exists in ERPNext
- Capacity > 0
```

**Cross-Check:**
```
✓ Tank created (TANK-00001)
✓ Fuel Type matches ERPNext Item Code
✓ Warehouse link is correct
✓ Capacity set appropriately
✓ Current Stock shows 0 (initially)
```

---

### Step 7: Create Dispensers

**Location:** `Petrol Pump V2 → Dispenser → New`

**Action:**
```yaml
Dispenser 1:
  Naming Series: DISP-
  Dispenser Name: Dispenser 1
  Petrol Pump: Main Pump Station
  Status: Active
  
  Nozzle Details (Child Table):
    Row 1:
      Nozzle Number: 1
      Fuel Type: PETROL-REGULAR (link to Item)
      Fuel Tank: TANK-00001 (link)
      Opening Reading: 0
      Current Reading: 0
    
    Row 2:
      Nozzle Number: 2
      Fuel Type: DIESEL
      Fuel Tank: TANK-00002
      Opening Reading: 0
      Current Reading: 0
```

**What Happens:**
- Creates dispenser machine master
- Links each nozzle to specific tank
- Tracks meter readings per nozzle
- Auto-naming: DISP-00001

**Cross-Check:**
```
✓ Dispenser created (DISP-00001)
✓ Each nozzle linked to correct fuel type
✓ Each nozzle linked to correct tank
✓ Opening readings set (usually 0 for new)
✓ Dispenser status = Active
```

---

### Step 8: Create Shifts

**Location:** `Petrol Pump V2 → Shift → New`

**Action:**
```yaml
Shift 1:
  Naming Series: SHIFT-
  Shift Name: Morning Shift
  Petrol Pump: Main Pump Station
  Start Time: 06:00:00
  End Time: 14:00:00
  Is Active: ✓

Shift 2:
  Naming Series: SHIFT-
  Shift Name: Evening Shift
  Petrol Pump: Main Pump Station
  Start Time: 14:00:00
  End Time: 22:00:00
  Is Active: ✓

Shift 3:
  Naming Series: SHIFT-
  Shift Name: Night Shift
  Petrol Pump: Main Pump Station
  Start Time: 22:00:00
  End Time: 06:00:00
  Is Active: ✓
```

**What Happens:**
- Defines work shifts
- Used in Shift Reading doctype
- Enables shift-wise reporting

**Cross-Check:**
```
✓ Shifts created (SHIFT-00001, SHIFT-00002, SHIFT-00003)
✓ No time overlaps between shifts
✓ All shifts marked active
```

---

### Step 9: Create Employees (ERPNext)

**Location:** `HR → Employee → New`

**Action:**
```yaml
Employee 1:
  Employee Name: Ahmed Khan
  Employee ID: EMP001
  Department: Operations
  Designation: Pump Accountant
  Status: Active
  Company: Your Company
```

**Cross-Check:**
```
✓ Employee created
✓ Linked to correct company
✓ Status = Active
```

---

### Step 10: Set Fuel Prices

**Location:** `Petrol Pump V2 → Fuel Price → New`

**Action:**
```yaml
Price 1:
  Naming Series: FPRICE-
  Fuel Type: PETROL-REGULAR (link to Item)
  Price Per Liter: 95.50
  Effective From: 2025-01-01 00:00:00
  Is Active: ✓

Price 2:
  Naming Series: FPRICE-
  Fuel Type: DIESEL
  Price Per Liter: 110.00
  Effective From: 2025-01-01 00:00:00
  Is Active: ✓
```

**What Happens:**
- Sets selling price for each fuel type
- Time-based pricing (effective from date)
- System automatically uses latest active price
- Auto-naming: FPRICE-00001

**Backend Logic:**
```python
# When fetching price:
def get_fuel_price(fuel_type, date):
    return frappe.db.get_value(
        "Fuel Price",
        {
            "fuel_type": fuel_type,
            "effective_from": ("<=", date),
            "is_active": 1
        },
        "price_per_liter",
        order_by="effective_from desc"
    )
```

**Cross-Check:**
```
✓ Price created for each fuel type
✓ Effective From date is correct
✓ Is Active = checked
✓ Price > 0
```

---

## Phase 2: Initial Stock Receipt

### Step 11: Receive Fuel via Purchase Receipt

**Location:** `ERPNext → Buying → Purchase Receipt → New`

**Action:**
```yaml
Purchase Receipt:
  Supplier: ABC Fuel Suppliers
  Posting Date: Today
  Company: Your Company
  Currency: PKR
  
  Items:
    Item Code: PETROL-REGULAR
    Quantity: 5000 Litres
    Rate: 90.00 PKR
    Amount: 450,000 PKR
    Warehouse: Main Pump - Storage
    
  Total: 450,000 PKR
  
  Submit ✓
```

**What Happens (Step by Step):**

1. **Stock Entry Auto-Created:**
   ```
   Purpose: Material Receipt
   To Warehouse: Main Pump - Storage
   Item: PETROL-REGULAR
   Qty: 5000 L
   Valuation Rate: 90.00
   Total Value: 450,000
   ```

2. **Stock Ledger Entry:**
   ```
   Item: PETROL-REGULAR
   Warehouse: Main Pump - Storage
   Qty Change: +5000
   Balance Qty: 5000
   Incoming Rate: 90.00
   Valuation Rate: 90.00
   Stock Value: 450,000
   ```

3. **Accounting Entry (GL):**
   ```
   Debit: Stock Asset Account          450,000
   Credit: Creditors (Supplier)        450,000
   ```

**Cross-Check:**

✅ **Check Purchase Receipt:**
```
Navigate to: Buying → Purchase Receipt → [PR-XXXXX]
Verify:
- Status = Submitted
- All items listed with quantities
- Total amount correct
```

✅ **Check Stock Balance:**
```
Navigate to: Stock → Stock Balance
Filter:
- Item: PETROL-REGULAR
- Warehouse: Main Pump - Storage

Should show:
- Balance Qty: 5000.00
- Balance Value: 450,000.00
- Valuation Rate: 90.00
```

✅ **Check Stock Ledger:**
```
Navigate to: Stock → Stock Ledger
Filter:
- Item: PETROL-REGULAR
- Warehouse: Main Pump - Storage
- Date: Today

Should show:
- Voucher Type: Purchase Receipt
- Actual Qty: +5000
- Qty After Transaction: 5000
- Stock Value: 450,000
- Valuation Rate: 90.00
```

✅ **Check General Ledger:**
```
Navigate to: Accounts → General Ledger
Filter: Today's date

Should see:
Account                     Debit       Credit
Stock Asset                 450,000     -
Creditors - ABC Fuel        -           450,000
```

---

### Step 12: Update Fuel Tank Stock

**Location:** `Petrol Pump V2 → Fuel Tank → TANK-00001`

**Action:**
1. Open the Fuel Tank record
2. Click **"Update Current Stock"** button (if available)
   
   OR
   
   The system automatically updates when you refresh

**What Happens:**
```python
# Backend code in fuel_tank.py:
def update_current_stock(self):
    """Fetch current stock from ERPNext warehouse"""
    if self.warehouse and self.fuel_type:
        stock_qty = get_stock_balance(
            self.fuel_type,  # Item Code
            self.warehouse,  # Warehouse
            posting_date=nowdate()
        )
        self.current_stock = flt(stock_qty)
        self.db_update()
```

**Cross-Check:**
```
✓ Fuel Tank → Current Stock now shows: 5000.00
✓ Matches Stock Balance in ERPNext
✓ Capacity not exceeded (5000 < 10000)
```

---

## Phase 3: Daily Operations

### Step 13: Morning - Dip Reading (Optional but Recommended)

**Location:** `Petrol Pump V2 → Dip Reading → New`

**Purpose:** Reconcile physical tank levels with system stock

**Action:**
```yaml
Dip Reading:
  Naming Series: DIP-
  Reading Date: Today
  Petrol Pump: Main Pump Station
  Employee: Ahmed Khan
  
  Dip Reading Details (Child Table):
    Row 1:
      Fuel Tank: TANK-00001 (Tank 1 - Petrol Regular)
      Measured Stock (Liters): 4950  # Physical dip stick reading
      System Stock (Liters): 5000    # Auto-fetched from ERPNext
      Variance (Liters): -50         # Auto-calculated
      Temperature (°C): 25
      Water Level (mm): 0
      Remarks: Minor evaporation loss
  
  Submit ✓
```

**What Happens (Step by Step):**

1. **Before Submit - Calculations:**
   ```python
   # In dip_reading.py:
   def validate(self):
       for d in self.dip_reading_details:
           # Fetch system stock
           d.system_stock = get_stock_balance(
               tank.fuel_type,
               tank.warehouse
           )
           
           # Calculate variance
           d.variance = flt(d.measured_stock) - flt(d.system_stock)
           # Variance = 4950 - 5000 = -50 liters
   ```

2. **On Submit - Stock Reconciliation Created:**
   ```python
   def on_submit(self):
       # If variance exists, create Stock Reconciliation
       if d.variance != 0:
           sr = frappe.new_doc("Stock Reconciliation")
           sr.purpose = "Stock Reconciliation"
           sr.posting_date = self.reading_date
           sr.company = company
           
           sr.append("items", {
               "item_code": fuel_type,
               "warehouse": warehouse,
               "qty": d.measured_stock,  # 4950
               "valuation_rate": current_valuation_rate,  # 90.00
               "current_qty": d.system_stock,  # 5000
               "current_valuation_rate": current_valuation_rate
           })
           
           sr.insert()
           sr.submit()
   ```

3. **Stock Reconciliation Posts:**
   ```
   Item: PETROL-REGULAR
   Warehouse: Main Pump - Storage
   Current Stock: 5000 L
   New Stock: 4950 L
   Difference: -50 L (shortage)
   Valuation Rate: 90.00
   Value Adjustment: -4,500
   ```

4. **Accounting Entry:**
   ```
   Debit: Stock Adjustment (Loss)      4,500
   Credit: Stock Asset                 4,500
   ```

5. **Update Fuel Tank:**
   ```python
   # Refresh tank stock
   tank.update_current_stock()
   # Current Stock now = 4950 L
   ```

**Cross-Check:**

✅ **Check Dip Reading:**
```
Navigate to: Dip Reading → DIP-00001
Verify:
- Status = Submitted
- Variance calculated correctly
- Stock Reconciliation Reference populated
```

✅ **Check Stock Reconciliation:**
```
Navigate to: Stock → Stock Reconciliation → [SR-XXXXX]
Verify:
- Purpose = Stock Reconciliation
- Item: PETROL-REGULAR
- Warehouse: Main Pump - Storage
- Current Qty: 5000
- Quantity: 4950
- Difference: -50
- Status = Submitted
```

✅ **Check Stock Balance:**
```
Stock → Stock Balance
Item: PETROL-REGULAR
Warehouse: Main Pump - Storage

Should now show:
- Balance Qty: 4950.00 (updated from 5000)
```

✅ **Check Fuel Tank:**
```
Fuel Tank → TANK-00001
Current Stock: 4950.00 (updated)
```

✅ **Check GL Entry:**
```
Accounts → General Ledger
Filter: Today, Account = Stock Adjustment

Debit: Stock Adjustment        4,500
Credit: Stock Asset            4,500
```

---

### Step 14: Sales Throughout the Day

**What Workers Do (NO System Access):**

```
Time: 06:00 - 22:00

At each nozzle:
1. Serve customers
2. Note meter readings periodically
3. Collect cash/card payments
4. Keep slips/receipts
5. For credit sales:
   - Note customer name
   - Note amount
   - Keep signed slip

At shift end (or day end):
- Workers give accountant:
  ✓ Final meter readings for all nozzles
  ✓ All cash collected
  ✓ All card slips
  ✓ Credit sales information
```

**Example Worker Notes:**

```
Nozzle 1 (Petrol Regular):
- Opening: 0
- Closing: 1500
- Liters: 1500

Nozzle 2 (Diesel):
- Opening: 0
- Closing: 800
- Liters: 800

Cash Collected: 180,000 PKR
Card Slips Total: 50,000 PKR
Credit Sales: 5,000 PKR (Customer: Ali Traders)
```

---

### Step 15: Evening - Day Closing Entry

**Location:** `Petrol Pump V2 → Day Closing → New`

**Action (Accountant enters data from workers):**

```yaml
Day Closing:
  Naming Series: DC-
  Reading Date: Today
  Petrol Pump: Main Pump Station
  Employee: Ahmed Khan (accountant)
  
  Nozzle Readings (Child Table):
    Row 1:
      Dispenser: DISP-00001
      Nozzle Number: 1
      Fuel Type: PETROL-REGULAR (auto-filled)
      Opening Reading: 0 (auto-fetched from last closing)
      Closing Reading: 1500 (entered by accountant)
      Dispensed Liters: 1500 (auto-calculated)
      Rate: 95.50 (auto-fetched from Fuel Price)
      Amount: 143,250 (auto-calculated)
    
    Row 2:
      Dispenser: DISP-00001
      Nozzle Number: 2
      Fuel Type: DIESEL
      Opening Reading: 0
      Closing Reading: 800
      Dispensed Liters: 800
      Rate: 110.00
      Amount: 88,000
  
  # Sales Summary (Auto-calculated):
  Total Sales: 231,250
  Total Liters: 2300
  
  # Payment Collection (Accountant enters):
  Cash Collected: 180,000
  Card/POS Amount: 50,000
  Credit Sales Amount: 1,250
  
  # Reconciliation (Auto-calculated):
  Total Payments Received: 230,000 (cash + card)
  Expected Collection: 230,000 (total sales - credit)
  Cash Variance: 0 (actual - expected)
  
  Submit ✓
```

**What Happens (Detailed Backend Flow):**

#### Phase 1: Validation (before_submit)

```python
def validate(self):
    # 1. Calculate nozzle sales
    for d in self.nozzle_readings:
        d.dispensed_liters = flt(d.closing_reading) - flt(d.opening_reading)
        
        # Fetch latest price
        d.rate = get_fuel_price(d.fuel_type, self.reading_date)
        
        d.amount = flt(d.dispensed_liters) * flt(d.rate)
    
    # 2. Calculate totals
    self.total_sales = sum(d.amount for d in self.nozzle_readings)
    self.total_liters = sum(d.dispensed_liters for d in self.nozzle_readings)
    
    # 3. Validate prices exist
    self.validate_prices()  # Throws error if no price found
    
    # 4. Validate stock availability
    self.validate_stock_availability()  # Ensures sufficient stock
    
    # 5. Calculate cash reconciliation
    self.calculate_cash_reconciliation()
```

#### Phase 2: Stock Entry Creation (on_submit)

```python
def on_submit(self):
    self.create_stock_entry()

def create_stock_entry(self):
    # Group by fuel type
    fuel_consumption = {
        'PETROL-REGULAR': 1500 L,
        'DIESEL': 800 L
    }
    
    # Create Stock Entry
    se = frappe.new_doc("Stock Entry")
    se.stock_entry_type = "Material Issue"
    se.purpose = "Material Issue"
    se.company = "Your Company"
    se.posting_date = "2025-01-15"
    
    # Add items
    se.append("items", {
        "s_warehouse": "Main Pump - Storage",
        "item_code": "PETROL-REGULAR",
        "qty": 1500,
        "basic_rate": 90.00,  # Fetched from Stock Ledger
        "amount": 135,000
    })
    
    se.append("items", {
        "s_warehouse": "Main Pump - Storage",
        "item_code": "DIESEL",
        "qty": 800,
        "basic_rate": 92.00,
        "amount": 73,600
    })
    
    se.insert()
    se.submit()
    
    # Save reference
    self.db_set('stock_entry_ref', se.name)
```

**Stock Entry Result:**
```
Stock Entry: STE-00001
Purpose: Material Issue
From Warehouse: Main Pump - Storage

Items:
1. PETROL-REGULAR: -1500 L @ 90.00 = -135,000
2. DIESEL: -800 L @ 92.00 = -73,600

Total Value: -208,600
```

**Stock Ledger Entries:**
```
Entry 1:
  Item: PETROL-REGULAR
  Warehouse: Main Pump - Storage
  Actual Qty: -1500
  Balance Qty: 3450 (4950 - 1500)
  Valuation Rate: 90.00
  Stock Value: 310,500

Entry 2:
  Item: DIESEL
  Warehouse: Main Pump - Storage
  Actual Qty: -800
  Balance Qty: varies
  Valuation Rate: 92.00
```

**Accounting Entry (COGS):**
```
Debit: Cost of Goods Sold       208,600
Credit: Stock Asset             208,600
```

#### Phase 3: Sales Invoice Creation

```python
def create_sales_invoice(self):
    # Get company and currency
    company = "Your Company"
    company_currency = "PKR"
    
    # Create customer if doesn't exist
    cash_customer = self.get_or_create_cash_customer(company)
    # Returns: "Cash Customer"
    
    # Group sales by fuel type
    fuel_sales = {
        'PETROL-REGULAR': {
            'qty': 1500,
            'rate': 95.50,
            'amount': 143,250
        },
        'DIESEL': {
            'qty': 800,
            'rate': 110.00,
            'amount': 88,000
        }
    }
    
    # Create Invoice
    si = frappe.new_doc("Sales Invoice")
    si.customer = "Cash Customer"
    si.company = company
    si.currency = company_currency
    si.posting_date = "2025-01-15"
    si.due_date = "2025-01-15"
    
    # Add items
    si.append("items", {
        "item_code": "PETROL-REGULAR",
        "qty": 1500,
        "rate": 95.50,
        "amount": 143,250
    })
    
    si.append("items", {
        "item_code": "DIESEL",
        "qty": 800,
        "rate": 110.00,
        "amount": 88,000
    })
    
    si.insert()
    si.submit()
    
    # Save reference
    self.db_set('sales_invoice_ref', si.name)
```

**Sales Invoice Result:**
```
Sales Invoice: SINV-00001
Customer: Cash Customer
Date: 2025-01-15
Currency: PKR

Items:
1. PETROL-REGULAR: 1500 L @ 95.50 = 143,250
2. DIESEL: 800 L @ 110.00 = 88,000

Grand Total: 231,250
Outstanding: 231,250
```

**Accounting Entry (Revenue):**
```
Debit: Debtors (Cash Customer)     231,250
Credit: Sales Revenue              231,250
```

#### Phase 4: Payment Entry Creation

```python
def create_payment_entry(self, sales_invoice, company):
    # Total payments = Cash + Card = 230,000
    # (Credit sales = 1,250 remains outstanding)
    
    company_currency = "PKR"
    
    pe = frappe.new_doc("Payment Entry")
    pe.payment_type = "Receive"
    pe.party_type = "Customer"
    pe.party = "Cash Customer"
    pe.company = company
    pe.posting_date = "2025-01-15"
    
    # Currency settings (CRITICAL!)
    pe.paid_from_account_currency = company_currency
    pe.paid_to_account_currency = company_currency
    pe.source_exchange_rate = 1.0
    pe.target_exchange_rate = 1.0
    
    # Accounts
    pe.paid_from = "Debtors - YC"
    pe.paid_to = "Cash - YC"
    
    # Amounts
    pe.paid_amount = 230,000
    pe.received_amount = 230,000
    
    # Link to invoice
    pe.append("references", {
        "reference_doctype": "Sales Invoice",
        "reference_name": "SINV-00001",
        "total_amount": 231,250,
        "outstanding_amount": 231,250,
        "allocated_amount": 230,000  # Partial payment
    })
    
    pe.insert()
    pe.submit()
    
    # Save reference
    self.db_set('payment_entry_ref', pe.name)
```

**Payment Entry Result:**
```
Payment Entry: PAY-00001
Party: Cash Customer
Type: Receive
Date: 2025-01-15

Paid From: Debtors - YC (PKR)
Paid To: Cash - YC (PKR)
Amount: 230,000

References:
- SINV-00001: 230,000 allocated

Unallocated: 1,250 (remains as outstanding)
```

**Accounting Entry (Payment):**
```
Debit: Cash - YC                   230,000
Credit: Debtors - YC               230,000
```

**Sales Invoice Updated:**
```
SINV-00001:
- Grand Total: 231,250
- Paid Amount: 230,000
- Outstanding: 1,250 (credit sales)
```

#### Phase 5: Update Nozzle Readings

```python
def update_nozzle_last_readings(self):
    for d in self.nozzle_readings:
        # Update nozzle's current_reading
        frappe.db.sql("""
            UPDATE `tabDispenser Nozzle Detail`
            SET current_reading = %s
            WHERE parent = %s AND nozzle_number = %s
        """, (d.closing_reading, d.dispenser, d.nozzle_number))
```

**Nozzle Updates:**
```
Dispenser: DISP-00001
  Nozzle 1: current_reading = 1500 (was 0)
  Nozzle 2: current_reading = 800 (was 0)

These become opening readings for tomorrow
```

#### Phase 6: Update Fuel Tank Stock

```python
def update_fuel_tank_stock(self):
    for tank in tanks_used:
        tank.update_current_stock()
        # Fetches latest from ERPNext
```

**Tank Updates:**
```
TANK-00001 (Petrol):
  Old Stock: 4950 L
  New Stock: 3450 L (4950 - 1500)

TANK-00002 (Diesel):
  Old Stock: varies
  New Stock: (old - 800)
```

---

**Complete Cross-Check After Day Closing Submission:**

### ✅ 1. Check Day Closing Document

```
Navigate to: Day Closing → DC-00001

Verify:
✓ Status = Submitted
✓ Total Sales = 231,250
✓ Total Liters = 2300
✓ Cash Variance = 0
✓ References populated:
  - stock_entry_ref = STE-00001
  - sales_invoice_ref = SINV-00001
  - payment_entry_ref = PAY-00001
```

### ✅ 2. Check Stock Entry

```
Navigate to: Stock → Stock Entry → STE-00001

Verify:
✓ Purpose = Material Issue
✓ Status = Submitted
✓ Source Warehouse = Main Pump - Storage
✓ Items:
  - PETROL-REGULAR: 1500 L @ 90.00
  - DIESEL: 800 L @ 92.00
✓ Total Value = 208,600
```

### ✅ 3. Check Stock Balance

```
Navigate to: Stock → Stock Balance
Filter: Item = PETROL-REGULAR, Warehouse = Main Pump - Storage

Verify:
✓ Balance Qty = 3450 L (was 4950 - 1500)
✓ Valuation Rate = 90.00
✓ Balance Value = 310,500
```

### ✅ 4. Check Sales Invoice

```
Navigate to: Accounts → Sales Invoice → SINV-00001

Verify:
✓ Customer = Cash Customer
✓ Currency = PKR
✓ Items:
  - PETROL-REGULAR: 1500 L @ 95.50 = 143,250
  - DIESEL: 800 L @ 110.00 = 88,000
✓ Grand Total = 231,250
✓ Outstanding = 1,250
✓ Paid Amount = 230,000
✓ Status = Submitted
```

### ✅ 5. Check Payment Entry

```
Navigate to: Accounts → Payment Entry → PAY-00001

Verify:
✓ Party = Cash Customer
✓ Paid From = Debtors - YC
✓ Paid To = Cash - YC
✓ Currency = PKR
✓ Exchange Rate = 1.0
✓ Paid Amount = 230,000
✓ Reference to SINV-00001
✓ Status = Submitted
```

### ✅ 6. Check General Ledger

```
Navigate to: Accounts → General Ledger
Filter: Voucher Date = Today

Should see THREE sets of entries:

Entry Set 1 - Stock Entry (COGS):
Account                        Debit       Credit
Cost of Goods Sold             208,600     -
Stock Asset                    -           208,600

Entry Set 2 - Sales Invoice (Revenue):
Account                        Debit       Credit
Debtors                        231,250     -
Sales Revenue                  -           231,250

Entry Set 3 - Payment Entry (Cash):
Account                        Debit       Credit
Cash                           230,000     -
Debtors                        -           230,000

NET EFFECT:
Cash:             +230,000 (Increased)
Debtors:          +1,250   (Outstanding credit)
Sales:            +231,250 (Revenue)
Stock Asset:      -208,600 (Inventory reduced)
COGS:             +208,600 (Expense)

PROFIT = Sales - COGS = 231,250 - 208,600 = 22,650
```

### ✅ 7. Check Fuel Tanks

```
Navigate to: Fuel Tank → TANK-00001

Verify:
✓ Current Stock = 3450 L (updated from 4950)
✓ Matches Stock Balance in ERPNext
```

### ✅ 8. Check Nozzle Readings

```
Navigate to: Dispenser → DISP-00001

Verify:
✓ Nozzle 1 → Current Reading = 1500
✓ Nozzle 2 → Current Reading = 800

These will be tomorrow's opening readings
```

### ✅ 9. Check Cash Book

```
Navigate to: Accounts → Cash Book
Filter: Date = Today, Account = Cash

Verify:
✓ Entry shows: +230,000
✓ Closing balance increased by 230,000
```

### ✅ 10. Check Profit & Loss

```
Navigate to: Accounts → Profit and Loss
Filter: Date Range = Today

Income:
  Sales Revenue:           231,250

Expenses:
  Cost of Goods Sold:      208,600

Gross Profit:              22,650

Profit Margin = 22,650 / 231,250 × 100 = 9.80%
```

---

## Phase 4: Shift-Based Operations

### Step 16: Shift Reading (Alternative to Day Closing)

**Use Case:** If you want to track sales per shift instead of per day

**Location:** `Petrol Pump V2 → Shift Reading → New`

**Action:**
```yaml
Shift Reading:
  Naming Series: SHREAD-
  Shift: SHIFT-00001 (Morning Shift)
  Petrol Pump: Main Pump Station
  Reading Date: Today
  Shift Start Time: 06:00:00
  Shift End Time: 14:00:00
  Employee: Worker Name
  
  Nozzle Readings:
    (Same structure as Day Closing)
    Enter readings for THIS SHIFT only
  
  Submit ✓
```

**What Happens:**
- Similar to Day Closing
- Creates Stock Entry for shift consumption
- Updates nozzle current readings
- Marks shift as "Closed"
- Does NOT create Sales Invoice/Payment (only Day Closing does that)

**Cross-Check:**
```
✓ SHREAD-00001 created
✓ Stock Entry created
✓ Stock reduced by shift sales
✓ Shift status = Closed
✓ Nozzle readings updated
```

---

## Phase 5: Quality Control

### Step 17: Fuel Testing

**Location:** `Petrol Pump V2 → Fuel Testing → New`

**Action:**
```yaml
Fuel Testing:
  Naming Series: FTEST-
  Test Date: Today
  Petrol Pump: Main Pump Station
  Testing Purpose: Quality Check
  
  Fuel Testing Details (Child Table):
    Row 1:
      Fuel Tank: TANK-00001
      Test Liters: 1
      Test Result: Pass
      Density: 0.75
      Flash Point: 40°C
      Remarks: Quality OK
  
  Total Test Liters: 1 (auto-sum)
  
  Submit ✓
```

**What Happens:**

1. **Stock Entry Created:**
   ```python
   se = frappe.new_doc("Stock Entry")
   se.purpose = "Material Issue"
   se.append("items", {
       "item_code": "PETROL-REGULAR",
       "s_warehouse": "Main Pump - Storage",
       "qty": 1,  # Test sample
       "basic_rate": 90.00,
       "amount": 90
   })
   se.submit()
   ```

2. **Stock Reduced:**
   ```
   PETROL-REGULAR stock: -1 L
   Value: -90 PKR
   ```

3. **Accounting Entry:**
   ```
   Debit: Testing Expense (or COGS)    90
   Credit: Stock Asset                 90
   ```

**Cross-Check:**
```
✓ FTEST-00001 created and submitted
✓ Stock Entry created
✓ Stock Balance reduced by 1 L
✓ Test results recorded
```

---

## Phase 6: Fuel Transfers

### Step 18: Fuel Transfer Between Tanks/Pumps

**Location:** `Petrol Pump V2 → Fuel Transfer → New`

**Action:**
```yaml
Fuel Transfer:
  Naming Series: FTRN-
  Transfer Date: Today
  From Petrol Pump: Main Pump Station
  From Tank: TANK-00001 (Petrol Regular)
  To Petrol Pump: Branch Pump
  To Tank: TANK-00010 (Petrol Regular at branch)
  Fuel Type: PETROL-REGULAR (must match both tanks)
  Transfer Liters: 500
  Vehicle Number: (if using tanker)
  Driver Name: (if applicable)
  Remarks: Stock transfer to branch
  
  Submit ✓
```

**What Happens:**

1. **Validation:**
   ```python
   # Ensures:
   - Fuel types match in both tanks
   - Sufficient stock in source tank
   - Transfer qty > 0
   ```

2. **Stock Entry Created:**
   ```python
   se = frappe.new_doc("Stock Entry")
   se.purpose = "Material Transfer"
   
   se.append("items", {
       "item_code": "PETROL-REGULAR",
       "s_warehouse": "Main Pump - Storage",      # From
       "t_warehouse": "Branch Pump - Storage",    # To
       "qty": 500,
       "basic_rate": 90.00
   })
   
   se.submit()
   ```

3. **Stock Ledger Entries:**
   ```
   Entry 1 (Source):
     Warehouse: Main Pump - Storage
     Qty: -500
     
   Entry 2 (Target):
     Warehouse: Branch Pump - Storage
     Qty: +500
   ```

4. **No Accounting Entry** (Internal transfer, no value change)

**Cross-Check:**
```
✓ FTRN-00001 created
✓ Stock Entry (Material Transfer) created
✓ Source tank stock: -500 L
✓ Target tank stock: +500 L
✓ Both at same valuation rate
```

---

## Phase 7: Corrections & Cancellations

### Step 19: Cancel Day Closing (If Error Found)

**Location:** Open the submitted Day Closing document

**Action:**
1. Click **Cancel** button
2. Confirm cancellation
3. Enter reason (optional)

**What Happens (Automatic Reversal):**

#### 1. Cancel Payment Entry
```python
def on_cancel(self):
    if self.payment_entry_ref:
        self.cancel_payment_entry()

def cancel_payment_entry(self):
    pe = frappe.get_doc("Payment Entry", self.payment_entry_ref)
    if pe.docstatus == 1:  # Submitted
        pe.cancel()
```

**Effect:**
- Payment Entry status → Cancelled
- Accounting reversal:
  ```
  Debit: Debtors        230,000
  Credit: Cash          230,000
  ```
- Cash balance reduced back
- Invoice outstanding increased

#### 2. Cancel Sales Invoice
```python
def cancel_sales_invoice(self):
    si = frappe.get_doc("Sales Invoice", self.sales_invoice_ref)
    if si.docstatus == 1:
        si.cancel()
```

**Effect:**
- Sales Invoice status → Cancelled
- Accounting reversal:
  ```
  Debit: Sales Revenue     231,250
  Credit: Debtors          231,250
  ```
- Revenue removed
- Debtors cleared

#### 3. Cancel Stock Entry
```python
def cancel_stock_entry(self):
    se = frappe.get_doc("Stock Entry", self.stock_entry_ref)
    if se.docstatus == 1:
        se.cancel()
```

**Effect:**
- Stock Entry status → Cancelled
- Stock Ledger reversal:
  ```
  PETROL-REGULAR: +1500 L (stock restored)
  DIESEL: +800 L
  ```
- Accounting reversal:
  ```
  Debit: Stock Asset       208,600
  Credit: COGS             208,600
  ```
- Stock value restored

#### 4. Revert Nozzle Readings
```python
def revert_nozzle_readings(self):
    for d in self.nozzle_readings:
        frappe.db.sql("""
            UPDATE `tabDispenser Nozzle Detail`
            SET current_reading = %s
            WHERE parent = %s AND nozzle_number = %s
        """, (d.opening_reading, d.dispenser, d.nozzle_number))
```

**Effect:**
- Nozzle 1: 1500 → 0 (reverted)
- Nozzle 2: 800 → 0 (reverted)

#### 5. Update Fuel Tank Stock
```python
# Refresh from ERPNext
for tank in tanks:
    tank.update_current_stock()
```

**Effect:**
- Tank stock updated to current ERPNext balance
- Shows restored quantities

**Complete Reversal Cross-Check:**

```
✓ Day Closing: Status = Cancelled
✓ Payment Entry: Status = Cancelled
✓ Sales Invoice: Status = Cancelled
✓ Stock Entry: Status = Cancelled
✓ Stock Balance: Restored to pre-closing amount
✓ Cash Balance: Reduced back
✓ Sales Revenue: Reversed
✓ COGS: Reversed
✓ Nozzle Readings: Reset to opening
✓ Fuel Tank: Stock restored
```

**Create Amended Version:**
1. Click **Amend** button on cancelled document
2. New document created with same data
3. Correct the errors
4. Submit the amended version

---

## Phase 8: Reports & Reconciliation

### Daily Checks

#### 1. Stock Balance Report

**Location:** `Stock → Stock Balance`

**Filters:**
- Date: Today
- Item: PETROL-REGULAR (or all)
- Warehouse: Main Pump - Storage

**What to Check:**
```
✓ Balance Qty matches physical tank level
✓ Valuation Rate is correct
✓ Balance Value = Qty × Rate
```

#### 2. Stock Ledger

**Location:** `Stock → Stock Ledger`

**Filters:**
- Item: PETROL-REGULAR
- Warehouse: Main Pump - Storage
- Date: Today

**What to Check:**
```
✓ All stock movements listed:
  - Purchase Receipt (receipts)
  - Day Closing Stock Entry (consumption)
  - Dip Reading Stock Reconciliation (adjustments)
  - Fuel Testing (samples)
  - Fuel Transfer (movements)
✓ Actual Qty column shows +/- changes
✓ Balance Qty After Transaction is correct
✓ Valuation Rate consistent
```

#### 3. General Ledger

**Location:** `Accounts → General Ledger`

**Filters:**
- Voucher Date: Today
- Account: All

**What to Check:**
```
✓ Stock Asset account: Increases with receipts, decreases with sales
✓ COGS account: Increases with sales
✓ Sales Revenue account: Increases with sales
✓ Cash account: Increases with payments received
✓ Debtors account: Outstanding credit sales
✓ All debits = All credits (accounting equation balanced)
```

#### 4. Profit & Loss Statement

**Location:** `Accounts → Profit and Loss`

**Filters:**
- Period: This Month (or Today)

**What to Check:**
```
Income:
  Sales Revenue: XXX

Expenses:
  Cost of Goods Sold: XXX
  Operating Expenses: XXX

Gross Profit = Sales - COGS
Net Profit = Gross Profit - Operating Expenses

Verify:
✓ Sales matches total Day Closing sales
✓ COGS matches stock consumption value
✓ Profit margin is reasonable (typically 5-15% for fuel)
```

#### 5. Cash Position

**Location:** `Accounts → Cash Flow Statement` or `General Ledger (Cash account)`

**What to Check:**
```
Opening Cash Balance: XXX
+ Cash Collected (from Payment Entries): +230,000
- Cash Payments (expenses, purchases): -XXX
Closing Cash Balance: XXX

✓ Closing balance should match physical cash on hand
✓ If variance, investigate missing/excess cash
```

#### 6. Accounts Receivable (Credit Sales)

**Location:** `Accounts → Accounts Receivable`

**What to Check:**
```
Customer: Cash Customer
Outstanding Amount: 1,250 (from credit sales)
Aging: 0-30 days

✓ Matches Day Closing credit sales amount
✓ Can be collected later via separate Payment Entry
```

---

## Critical Cross-Checks

### Daily Reconciliation Checklist

#### ✅ Physical vs System Stock

**Process:**
1. Perform physical dip reading of all tanks
2. Compare with Stock Balance report in ERPNext
3. If variance:
   - Create Dip Reading to reconcile
   - Investigate cause (theft, evaporation, spillage, metering error)

**Expected Variances:**
- Evaporation: 0.1-0.5% loss (acceptable)
- Temperature effect: Minor expansion/contraction
- Metering error: Should be < 0.1%

**Red Flags:**
- Variance > 1% : Investigate immediately
- Consistent shortages: Check for leakage or theft
- Consistent excess: Check meter calibration

#### ✅ Cash Reconciliation

**Process:**
1. Count physical cash
2. Compare with Day Closing "Cash Collected"
3. Compare with Cash Account balance in ERPNext

**Formula:**
```
Expected Cash = Opening Cash + Today's Collections - Today's Payments

If Physical Cash ≠ Expected Cash:
  Variance = Physical - Expected
  
  If Variance > 0: Cash excess (investigate)
  If Variance < 0: Cash shortage (investigate)
```

**Resolution:**
- Small variances (< 1%): May be counting errors, petty cash
- Large variances: Require approval, investigation

#### ✅ Nozzle Meter vs Sales

**Process:**
```
For each nozzle:
  Liters Sold = Closing Reading - Opening Reading
  Expected Sales = Liters × Price Per Liter
  
  Verify:
  ✓ Liters calculation is correct
  ✓ Price used is current active price
  ✓ Amount = Liters × Price (no arithmetic errors)
```

#### ✅ Accounting Equation

**Always Verify:**
```
Assets = Liabilities + Equity

In ERPNext:
  Balance Sheet should always balance
  
If not balanced:
  - Check for GL Entry errors
  - Verify all transactions posted correctly
  - Contact system administrator
```

#### ✅ Stock Value

**Process:**
```
For each item:
  Stock Value = Stock Qty × Valuation Rate
  
  Verify in Stock Balance report:
  ✓ Balance Value = Balance Qty × Valuation Rate
  ✓ Valuation method (FIFO/Moving Avg) applied correctly
  ✓ No negative stock values
```

---

## Complete Testing Scenario

### Full Day Test Workflow

#### Setup (One Time)
```
1. ✓ Create Company with default currency
2. ✓ Create Items (PETROL-REGULAR, DIESEL)
3. ✓ Create Warehouses (Main Pump - Storage)
4. ✓ Create Petrol Pump (Main Pump Station)
5. ✓ Create Fuel Types
6. ✓ Create Fuel Tanks (TANK-00001, TANK-00002)
7. ✓ Create Dispensers with Nozzles
8. ✓ Create Shifts
9. ✓ Create Employees
10. ✓ Set Fuel Prices
```

#### Day 1: Initial Stock Receipt
```
1. Purchase Receipt: 10,000 L Petrol @ 90 PKR
2. Purchase Receipt: 8,000 L Diesel @ 92 PKR
3. Verify Stock Balance shows correct quantities
4. Update Fuel Tank current stock
```

#### Day 2: First Day of Operations
```
Morning:
1. Create Dip Reading (optional)
   - Petrol: 10,000 L (no variance)
   - Diesel: 8,000 L (no variance)

Throughout Day:
2. Workers sell fuel and note readings

Evening:
3. Create Day Closing
   - Nozzle 1: 0 → 1500 L (Petrol)
   - Nozzle 2: 0 → 800 L (Diesel)
   - Cash: 180,000
   - Card: 50,000
   - Credit: 1,250
   - Submit

4. Verify All Creations:
   ✓ Stock Entry created
   ✓ Sales Invoice created
   ✓ Payment Entry created
   ✓ Stock reduced correctly
   ✓ Cash increased
   ✓ Nozzle readings updated

5. Check Reports:
   ✓ Stock Balance: Petrol = 8,500 L
   ✓ Stock Balance: Diesel = 7,200 L
   ✓ General Ledger: All entries posted
   ✓ P&L: Shows profit for the day
   ✓ Cash Book: Shows cash increase
```

#### Day 3: Test Cancellation
```
1. Open DC-00001
2. Cancel the document
3. Verify Reversals:
   ✓ Payment cancelled
   ✓ Invoice cancelled
   ✓ Stock Entry cancelled
   ✓ Stock restored
   ✓ Nozzles reset

4. Create Amended Version:
   ✓ Correct any errors
   ✓ Submit
   ✓ Verify new entries created
```

#### Day 4: Test Fuel Transfer
```
1. Create Branch Pump
2. Create TANK-00003 at branch
3. Create Fuel Transfer:
   - From: TANK-00001 (Main Pump)
   - To: TANK-00003 (Branch)
   - Qty: 500 L
4. Verify:
   ✓ Main Pump stock: -500 L
   ✓ Branch stock: +500 L
   ✓ Stock Entry (Transfer) created
```

#### Day 5: Test Quality Testing
```
1. Create Fuel Testing
   - Tank: TANK-00001
   - Test Liters: 1
   - Result: Pass
2. Verify:
   ✓ Stock Entry created (Material Issue)
   ✓ Stock reduced by 1 L
   ✓ Test results recorded
```

---

## Troubleshooting Guide

### Common Errors and Solutions

#### Error 1: "Target Exchange Rate is mandatory"

**Cause:** Currency mismatch or missing currency settings

**Solution:**
1. Ensure Company has default currency set
2. Ensure Cash Customer has default currency
3. The system now automatically sets:
   - Sales Invoice currency = Company currency
   - Payment Entry exchange rates = 1.0

**Code Fix (Already Applied):**
```python
# In create_sales_invoice():
si.currency = company_currency

# In create_payment_entry():
pe.paid_from_account_currency = company_currency
pe.paid_to_account_currency = company_currency
pe.source_exchange_rate = 1.0
pe.target_exchange_rate = 1.0
```

#### Error 2: "Insufficient Stock"

**Cause:** Trying to sell more fuel than available in tank

**Solution:**
1. Check current stock in Fuel Tank
2. Check Stock Balance in ERPNext
3. If stock exists but not showing:
   - Click "Update Current Stock" on Fuel Tank
   - Verify warehouse link is correct
4. If genuinely insufficient:
   - Create Purchase Receipt to receive more stock

#### Error 3: "Fuel Price not found"

**Cause:** No active price for the fuel type on the transaction date

**Solution:**
1. Navigate to Fuel Price list
2. Verify active price exists for the fuel type
3. Ensure "Is Active" is checked
4. Ensure "Effective From" date is before/equal to transaction date
5. Create new Fuel Price if missing

#### Error 4: "Naming Series Already Exists (DC-00001)"

**Cause:** Naming series counter out of sync

**Solution:** (Already Fixed)
- All doctypes now use proper `naming_series:` field
- Counters automatically managed by ERPNext
- If still occurs, contact administrator

#### Error 5: "Valuation Rate is 0"

**Cause:** No stock ledger entry with valuation rate

**Solution:**
1. Ensure Purchase Receipt was submitted with proper rate
2. Check Stock Ledger Entry for the item
3. Verify "Maintain Stock" is enabled on Item
4. If using FIFO, ensure there's stock available
5. Create Purchase Receipt if no stock history exists

---

## Best Practices

### 1. Daily Operations

- ✅ **Always** perform Dip Reading in morning
- ✅ **Always** verify nozzle readings match worker notes
- ✅ **Always** count cash before entering Day Closing
- ✅ **Always** reconcile cash variance
- ✅ **Always** check reports after Day Closing

### 2. Data Entry

- ✅ **Never** skip required fields
- ✅ **Never** submit without verification
- ✅ **Never** cancel without reason
- ✅ **Always** use current date for transactions
- ✅ **Always** verify calculations

### 3. Security

- ✅ **Use** User Permissions to restrict pump access
- ✅ **Use** Role Permissions for workers vs accountants
- ✅ **Enable** two-factor authentication
- ✅ **Regular** password changes
- ✅ **Backup** database daily

### 4. Reconciliation

- ✅ **Daily** stock reconciliation
- ✅ **Daily** cash reconciliation
- ✅ **Weekly** customer credit review
- ✅ **Monthly** financial statements review
- ✅ **Monthly** variance analysis

### 5. Maintenance

- ✅ **Regular** nozzle meter calibration
- ✅ **Regular** tank cleaning (affects dip readings)
- ✅ **Regular** system backups
- ✅ **Regular** ERPNext updates
- ✅ **Monthly** data archival

---

## Appendix

### A. Keyboard Shortcuts

- `Ctrl + S`: Save document
- `Ctrl + Enter`: Submit document (after save)
- `Ctrl + G`: Get latest prices/values
- `Ctrl + K`: Add new row in child table
- `Ctrl + D`: Duplicate row in child table

### B. Important Accounts (Chart of Accounts)

```
Assets
  ├─ Current Assets
  │   ├─ Cash
  │   │   └─ Cash - YC
  │   ├─ Bank Accounts
  │   ├─ Debtors
  │   │   └─ Debtors - YC
  │   └─ Stock Assets
  │       └─ Stock Asset - YC

Liabilities
  └─ Current Liabilities
      └─ Creditors
          └─ Creditors - YC

Income
  └─ Direct Income
      └─ Sales Revenue
          └─ Fuel Sales - YC

Expenses
  ├─ Cost of Goods Sold
  │   └─ COGS - Fuel - YC
  ├─ Operating Expenses
  └─ Stock Adjustment
      └─ Stock Loss/Gain - YC
```

### C. Common Formulas

**Gross Profit:**
```
Gross Profit = Total Sales - COGS
Gross Profit % = (Gross Profit / Total Sales) × 100
```

**Fuel Consumption:**
```
Consumption = Opening Stock + Purchases - Closing Stock
```

**Cash Variance:**
```
Variance = (Cash + Card) - (Total Sales - Credit Sales)
```

**Profit Per Liter:**
```
Profit/L = (Selling Price - Cost Price)
```

**Tank Utilization:**
```
Utilization % = (Current Stock / Capacity) × 100
```

---

**Document Version:** 2.0  
**Last Updated:** 2025-01-27  
**Author:** Petrol Pump V2 Development Team

---

For more information, see [README.md](README.md)

