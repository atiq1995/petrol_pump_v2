# ⛽ Petrol Pump Management System V2

A comprehensive **Frappe/ERPNext** application for managing petrol pump operations, inventory, sales, and accounting. Designed specifically for fuel stations with multiple dispensers, tanks, and real-time stock tracking.

[![ERPNext](https://img.shields.io/badge/ERPNext-v14+-blue.svg)](https://erpnext.com)
[![Frappe](https://img.shields.io/badge/Frappe-Framework-orange.svg)](https://frappeframework.com)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

---

## 📋 Table of Contents

- [Features](#-features)
- [System Architecture](#-system-architecture)
- [Installation](#-installation)
- [Configuration](#-configuration)
- [Usage Flow](#-usage-flow)
- [Doctypes Overview](#-doctypes-overview)
- [ERPNext Integration](#-erpnext-integration)
- [Business Logic](#-business-logic)
- [Reports](#-reports)
- [Screenshots](#-screenshots)
- [Contributing](#-contributing)
- [License](#-license)

---

## ✨ Features

### 🎯 Core Functionality

- **Multi-Pump Management**: Manage multiple petrol stations from a single system
- **Real-Time Inventory Tracking**: Live stock updates synchronized with ERPNext
- **Automated Accounting**: Automatic journal entries for sales, COGS, and payments
- **Nozzle-Level Metering**: Track individual nozzle readings and sales
- **Shift Management**: Support for multiple shifts with shift-wise reporting
- **Fuel Quality Testing**: Record quality tests with automatic stock adjustments
- **Inter-Pump Transfers**: Transfer fuel between tanks/locations
- **Physical Stock Reconciliation**: Dip reading reconciliation with system stock
- **Cash Reconciliation**: Daily cash counting with variance tracking
- **Credit Sales Management**: Track credit sales with customer-wise records
- **Dynamic Pricing**: Time-based fuel pricing with effective date management
- **Audit Trail**: Complete change tracking for compliance

### 🔧 Technical Features

- **Proper Naming Series**: Standard ERPNext naming conventions
- **Submittable Documents**: Approval workflow with cancellation support
- **Stock Entry Integration**: Automatic Material Issue/Receipt/Transfer
- **Sales Invoice Generation**: Auto-create invoices for daily sales
- **Payment Entry**: Automatic payment reconciliation
- **Valuation Rate Tracking**: FIFO/Moving Average costing
- **Multi-Currency Support**: Built-in currency handling
- **Role-Based Permissions**: Secure access control
- **Cancellation Reversal**: Proper cleanup on document cancellation

---

## 🏗️ System Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    PETROL PUMP V2 APP                        │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐     │
│  │   MASTER     │  │  OPERATIONS  │  │ TRANSACTIONS │     │
│  │     DATA     │  │              │  │              │     │
│  └──────────────┘  └──────────────┘  └──────────────┘     │
│         │                 │                  │              │
│         ▼                 ▼                  ▼              │
│  • Petrol Pump    • Day Closing     • Stock Entries        │
│  • Fuel Type      • Shift Reading   • Sales Invoices       │
│  • Fuel Tank      • Dip Reading     • Payment Entries      │
│  • Dispenser      • Fuel Testing    • Stock Reconciliation │
│  • Fuel Price     • Fuel Transfer   • Journal Entries      │
│  • Shift          •                 •                      │
│                                                              │
└──────────────────┬───────────────────────────────────────────┘
                   │
                   ▼
┌─────────────────────────────────────────────────────────────┐
│                      ERPNext CORE                            │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  Stock Module          Accounts Module      Sales Module    │
│  • Item Master         • Chart of Accounts  • Customer      │
│  • Warehouse           • GL Entries         • Invoice       │
│  • Stock Ledger        • Payment Entry      • Pricing       │
│  • Valuation           • Reconciliation     •               │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

---

## 📦 Installation

### Prerequisites

- **Frappe Framework** v14 or higher
- **ERPNext** v14 or higher
- **MariaDB** 10.3+
- **Python** 3.10+
- **Node.js** 16+

### Step 1: Get the App

```bash
# Navigate to your Frappe bench
cd ~/frappe-bench

# Get the app from GitHub
bench get-app https://github.com/YOUR_USERNAME/petrol_pump_v2.git
```

### Step 2: Install on Site

```bash
# Install app on your site
bench --site YOUR_SITE_NAME install-app petrol_pump_v2

# Run migrations
bench --site YOUR_SITE_NAME migrate

# Clear cache
bench --site YOUR_SITE_NAME clear-cache
```

### Step 3: Restart Services

```bash
# Restart bench
bench restart

# If using production
sudo service nginx reload
sudo supervisorctl restart all
```

---

## ⚙️ Configuration

### 1. Initial Setup

Navigate to **Setup → Petrol Pump V2** and configure:

#### A. Create Company (ERPNext Standard)
```
Setup → Company
- Company Name
- Default Currency: PKR (or your currency)
- Country
- Default Accounts (Cash, Bank, Receivable, etc.)
```

#### B. Create Fuel Items (ERPNext)
```
Stock → Item → New Item
For each fuel type:
- Item Code: PETROL-REGULAR
- Item Name: Petrol Regular
- Item Group: Fuel
- Stock UOM: Litre
- Valuation Method: FIFO or Moving Average
- Maintain Stock: ✓ Yes
```

#### C. Create Warehouses (ERPNext)
```
Stock → Warehouse
For each pump:
- Warehouse Name: Main Pump - Storage
- Parent Warehouse: (optional)
- Company: Your Company
```

### 2. Master Data Setup

#### Create Petrol Pump
```
Petrol Pump V2 → Petrol Pump → New
- Petrol Pump Name
- Company
- Address
- Contact Details
```

#### Create Fuel Types
```
Petrol Pump V2 → Fuel Type → New
- Fuel Type Name: Petrol Regular
- Description
```

#### Create Fuel Tanks
```
Petrol Pump V2 → Fuel Tank → New
- Tank Name
- Petrol Pump
- Fuel Type (link to ERPNext Item)
- Warehouse (link to ERPNext Warehouse)
- Capacity (Liters)
```

#### Create Dispensers & Nozzles
```
Petrol Pump V2 → Dispenser → New
- Dispenser Name
- Petrol Pump
- Status: Active
- Nozzle Details (child table):
  - Nozzle Number
  - Fuel Type
  - Fuel Tank
  - Opening Reading
```

#### Set Fuel Prices
```
Petrol Pump V2 → Fuel Price → New
- Fuel Type
- Price Per Liter
- Effective From
- Is Active: ✓
```

---

## 🔄 Usage Flow

See [FLOW.md](FLOW.md) for detailed step-by-step operations guide.

### Quick Start Workflow

```
1. Setup Master Data (One-time)
   └─> Pump → Tanks → Dispensers → Nozzles → Prices

2. Receive Fuel (Purchase Receipt in ERPNext)
   └─> Creates Stock Entry → Updates Warehouse Stock

3. Daily Operations:
   a. Morning: Dip Reading (Optional)
      └─> Reconciles Physical vs System Stock
   
   b. Sales Throughout Day
      └─> Workers note nozzle readings
   
   c. Evening: Day Closing
      └─> Creates Stock Entry (fuel consumed)
      └─> Creates Sales Invoice (revenue)
      └─> Creates Payment Entry (cash collection)
      └─> Updates Nozzle Readings
      └─> Posts Accounting Entries

4. Reports & Reconciliation
   └─> Check Stock Balance
   └─> Check Cash Position
   └─> Check Profit & Loss
```

---

## 📚 Doctypes Overview

### Master Data

| DocType | Purpose | Submittable |
|---------|---------|-------------|
| **Petrol Pump** | Branch/Location master | No |
| **Fuel Type** | Fuel product master | No |
| **Fuel Tank** | Underground tank tracking | No |
| **Dispenser** | Dispenser machine master | No |
| **Fuel Price** | Pricing history | No |
| **Shift** | Work shift definitions | No |

### Operational Documents

| DocType | Purpose | Submittable | Auto-Creates |
|---------|---------|-------------|--------------|
| **Day Closing** | Daily sales & stock consumption | Yes | Stock Entry, Sales Invoice, Payment Entry |
| **Shift Reading** | Shift-wise sales tracking | Yes | Stock Entry |
| **Dip Reading** | Physical stock reconciliation | Yes | Stock Reconciliation |
| **Fuel Testing** | Quality testing samples | Yes | Stock Entry (Material Issue) |
| **Fuel Transfer** | Inter-tank/pump transfers | Yes | Stock Entry (Material Transfer) |

### Child Tables

| DocType | Parent | Purpose |
|---------|--------|---------|
| **Nozzle Reading Detail** | Day Closing / Shift Reading | Individual nozzle sales |
| **Fuel Testing Detail** | Fuel Testing | Test results per tank |
| **Dispenser Nozzle Detail** | Dispenser | Nozzle configuration |
| **Dip Reading Detail** | Dip Reading | Tank-wise physical stock |

---

## 🔗 ERPNext Integration

### Stock Module Integration

```python
# Automatic Stock Entry Creation
Day Closing → on_submit() → create_stock_entry()
  ├─> Purpose: Material Issue
  ├─> Item: Fuel Type (from ERPNext Item)
  ├─> Warehouse: From Fuel Tank linked warehouse
  ├─> Qty: Total liters dispensed
  ├─> Valuation Rate: From Stock Ledger (FIFO/Moving Avg)
  └─> Posts: Debit COGS, Credit Stock Asset
```

### Accounts Module Integration

```python
# Sales Invoice
Day Closing → on_submit() → create_sales_invoice()
  ├─> Customer: Cash Customer (auto-created)
  ├─> Items: Fuel types with quantities
  ├─> Rate: From Fuel Price master
  └─> Posts: Debit Debtors, Credit Sales

# Payment Entry
Day Closing → on_submit() → create_payment_entry()
  ├─> Party: Cash Customer
  ├─> Paid From: Debtors
  ├─> Paid To: Cash Account
  └─> Posts: Debit Cash, Credit Debtors
```

### Stock Reconciliation

```python
# Physical Stock Adjustment
Dip Reading → on_submit() → create_stock_reconciliation()
  ├─> Item: Fuel Type
  ├─> Warehouse: From Tank
  ├─> Current Stock: System balance
  ├─> Measured Stock: Dip reading
  ├─> Variance: Difference
  └─> Posts: Stock adjustment with valuation
```

---

## 💼 Business Logic

### 1. Stock Consumption Calculation

```
Total Liters Sold = Σ (Closing Reading - Opening Reading) for all nozzles
```

### 2. Sales Calculation

```
Per Nozzle:
  Liters Sold = Closing Reading - Opening Reading
  Amount = Liters Sold × Price Per Liter

Total Sales = Σ (Amount for all nozzles)
```

### 3. Cash Reconciliation

```
Total Payments Received = Cash + Card
Expected Collection = Total Sales - Credit Sales
Cash Variance = Total Payments Received - Expected Collection

If Variance ≠ 0:
  → Flag for approval (future feature)
```

### 4. Stock Valuation (COGS)

```
For each fuel type sold:
  COGS = Quantity Sold × Valuation Rate
  
Valuation Rate fetched from:
  Stock Ledger Entry (latest for item + warehouse)
  
Accounting Entry:
  Dr. Cost of Goods Sold: COGS Amount
  Cr. Stock Asset: COGS Amount
```

### 5. Profit Calculation

```
Gross Profit = Total Sales - COGS
Profit Margin % = (Gross Profit / Total Sales) × 100
```

---

## 📊 Reports

### Standard ERPNext Reports

Access these from ERPNext:

1. **Stock Balance** - Current stock per tank/warehouse
2. **Stock Ledger** - All stock movements with dates
3. **Stock Analytics** - Stock trends and consumption
4. **General Ledger** - All accounting entries
5. **Profit and Loss** - Revenue vs expenses
6. **Balance Sheet** - Assets, liabilities, equity
7. **Accounts Receivable** - Outstanding credit sales
8. **Sales Register** - All sales invoices

### Custom Reports (Planned)

- Daily Sales Summary by Pump
- Nozzle-wise Sales Analysis
- Fuel Consumption Trends
- Cash Variance Report
- Shift Performance Report
- Tank Capacity Utilization

---

## 🔐 Security & Permissions

### Role-Based Access

| Role | Permissions |
|------|------------|
| **System Manager** | Full access to all doctypes |
| **Accountant** | Create/Submit operational docs, Read masters |
| **Pump Manager** | Create operational docs, Read-only submission |
| **Worker** | No system access (provide readings to accountant) |

### User Permissions

```python
# Restrict users to specific pumps
Setup → User Permissions
- User: accountant@pump.com
- Allow: Petrol Pump
- For Value: Main Pump Station
```

This ensures accountants only see data for their assigned pump.

---

## 🧪 Testing

### Test Scenario 1: Complete Day Flow

```bash
# 1. Create test data
- Company: Test Company
- Item: TEST-PETROL
- Warehouse: Test Warehouse
- Petrol Pump: Test Pump
- Fuel Tank: TEST-TANK-001
- Dispenser: TEST-DISP-001
- Fuel Price: 95.50 PKR/L

# 2. Receive stock
Purchase Receipt: 10,000L @ 90 PKR/L

# 3. Day Closing
Day Closing:
  - Nozzle 1: 0 → 1500L sold
  - Cash: 100,000
  - Total Sales: 143,250

# 4. Verify
✓ Stock reduced by 1500L
✓ Sales Invoice created
✓ Payment Entry created
✓ GL Entries posted
✓ Cash increased
✓ Profit = (1500 × 95.50) - (1500 × 90) = 8,250
```

---

## 🐛 Troubleshooting

### Common Issues

#### 1. "Target Exchange Rate is mandatory"
**Solution**: Already fixed! Ensure:
- Company has default currency set
- Cash Customer has default currency
- Update via: `bench --site SITE migrate`

#### 2. Naming Series "Already Exists"
**Solution**: Fixed with proper naming series implementation
- All doctypes now use `naming_series:` with Select field

#### 3. Stock Balance Mismatch
**Solution**: 
- Run Dip Reading to reconcile
- Click "Update Current Stock" on Fuel Tank
- Check Stock Ledger for unauthorized entries

#### 4. Valuation Rate = 0
**Solution**:
- Ensure Purchase Receipt submitted with proper rate
- Check Stock Ledger Entry for valuation_rate
- Verify Item has "Maintain Stock" enabled

---

## 📖 Documentation

- [FLOW.md](FLOW.md) - Detailed operational flow
- [API Documentation](docs/API.md) - Developer API reference (planned)
- [Customization Guide](docs/CUSTOMIZATION.md) - How to customize (planned)

---

## 🤝 Contributing

Contributions are welcome! Please follow these steps:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

### Development Setup

```bash
# Clone your fork
git clone https://github.com/YOUR_USERNAME/petrol_pump_v2.git

# Create development site
bench new-site dev.local
bench --site dev.local install-app petrol_pump_v2

# Start development server
bench start
```

---

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

## 👥 Authors

- **Your Name** - *Initial work* - [GitHub Profile](https://github.com/YOUR_USERNAME)

---

## 🙏 Acknowledgments

- Built on [Frappe Framework](https://frappeframework.com)
- Powered by [ERPNext](https://erpnext.com)
- Thanks to the Frappe community

---

## 📞 Support

- **Issues**: [GitHub Issues](https://github.com/YOUR_USERNAME/petrol_pump_v2/issues)
- **Discussions**: [GitHub Discussions](https://github.com/YOUR_USERNAME/petrol_pump_v2/discussions)
- **Email**: your.email@example.com

---

## 🗺️ Roadmap

### Version 2.0 (Planned)
- [ ] Credit Customer Management with detailed tracking
- [ ] Cash Variance Approval Workflow
- [ ] Period Locking for month-end
- [ ] Bank Deposit Tracking
- [ ] Advanced Analytics Dashboard
- [ ] Mobile App for Workers
- [ ] SMS/Email Alerts
- [ ] Multi-Branch Consolidated Reports

### Version 2.1 (Future)
- [ ] Loyalty Program Integration
- [ ] Supplier Portal
- [ ] Automated Reorder Points
- [ ] Predictive Analytics
- [ ] IoT Sensor Integration
- [ ] Real-time Nozzle Reading Capture

---

## 📈 Statistics

- **Doctypes**: 11 (6 Masters + 5 Operational)
- **ERPNext Integration Points**: 5 (Stock Entry, Sales Invoice, Payment Entry, Stock Reconciliation, Item)
- **Supported Operations**: Day Closing, Shift Reading, Dip Reading, Fuel Testing, Fuel Transfer
- **Industries**: Fuel Retail, Petrol Stations, Gas Stations

---

**Built with ❤️ for the Petrol Pump Industry**
