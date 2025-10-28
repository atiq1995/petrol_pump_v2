# 📊 Petrol Pump V2 - Reports Documentation

This document describes all available reports in the Petrol Pump Management System V2.

---

## 📋 Table of Contents

1. [Daily Sales Summary](#1-daily-sales-summary)
2. [Nozzle Performance](#2-nozzle-performance)
3. [Stock Variance Analysis](#3-stock-variance-analysis)
4. [Cash Reconciliation Report](#4-cash-reconciliation-report)
5. [Fuel Consumption Trends](#5-fuel-consumption-trends)
6. [Pump Performance Comparison](#6-pump-performance-comparison)
7. [Shift Profitability Analysis](#7-shift-profitability-analysis)
8. [Tank Utilization Report](#8-tank-utilization-report)
9. [Profit Analysis Report](#9-profit-analysis-report)
10. [Monthly Summary Report](#10-monthly-summary-report)
11. [Shift Consumption Summary](#11-shift-consumption-summary) *(Existing)*

---

## 1. Daily Sales Summary

**Purpose:** Track daily sales performance across all pumps

**Base DocType:** Day Closing

**Features:**
- ✅ Sales by date and pump
- ✅ Payment breakdown (Cash, Card, Credit)
- ✅ Cash variance tracking
- ✅ Profit calculation with margins
- ✅ Visual chart showing sales & profit trends

**Filters:**
- From Date
- To Date
- Petrol Pump

**Key Metrics:**
- Total Sales (Revenue)
- Total Liters Sold
- Cash/Card/Credit breakdown
- Estimated Profit
- Profit Margin %
- Cash Variance

**Use Case:**
Daily management review to track sales performance, identify cash discrepancies, and monitor profitability.

---

## 2. Nozzle Performance

**Purpose:** Analyze individual nozzle performance

**Base DocType:** Day Closing (Nozzle Reading Detail)

**Features:**
- ✅ Sales per nozzle
- ✅ Fuel type breakdown
- ✅ Average daily performance
- ✅ Identify top/bottom performers
- ✅ Bar chart showing top 10 nozzles

**Filters:**
- From Date
- To Date
- Petrol Pump
- Fuel Type

**Key Metrics:**
- Total Liters per nozzle
- Total Sales per nozzle
- Average per day (liters)
- Number of days active

**Use Case:**
Identify which nozzles are performing well or having issues. Helps in maintenance planning and dispenser optimization.

---

## 3. Stock Variance Analysis

**Purpose:** Monitor physical vs system stock differences

**Base DocType:** Dip Reading

**Features:**
- ✅ Physical vs system stock comparison
- ✅ Variance in liters and value
- ✅ Percentage variance calculation
- ✅ Status indicators (Perfect/Normal/Alert/Critical)
- ✅ Trend chart for variance tracking

**Filters:**
- From Date
- To Date
- Petrol Pump
- Fuel Tank

**Key Metrics:**
- System Stock (from ERPNext)
- Physical Stock (dip reading)
- Variance (liters)
- Variance %
- Value Impact (PKR)
- Status

**Status Categories:**
- **Perfect:** 0% variance
- **Normal:** < 0.5% variance
- **Alert:** 0.5% - 1% variance
- **Critical:** > 1% variance

**Use Case:**
Loss prevention, theft detection, evaporation tracking, meter calibration monitoring.

---

## 4. Cash Reconciliation Report

**Purpose:** Daily cash management and variance tracking

**Base DocType:** Day Closing

**Features:**
- ✅ Expected vs actual cash collection
- ✅ Variance tracking per accountant
- ✅ Status indicators for variance levels
- ✅ Summary cards (Total Variance, Perfect Days, Critical Days)
- ✅ Variance trend chart

**Filters:**
- From Date
- To Date
- Petrol Pump
- Employee (Accountant)

**Key Metrics:**
- Total Sales
- Cash Collected
- Card Amount
- Credit Sales
- Expected Collection
- Cash Variance
- Variance %
- Status

**Variance Status:**
- **Perfect:** Zero variance
- **Minor:** < PKR 100
- **Alert:** PKR 100 - 500
- **Critical:** > PKR 500

**Use Case:**
Daily cash control, accountant performance monitoring, fraud prevention, cash flow management.

---

## 5. Fuel Consumption Trends

**Purpose:** Understand fuel sales patterns and trends

**Base DocType:** Day Closing (Nozzle Reading Detail)

**Features:**
- ✅ Fuel-wise consumption analysis
- ✅ Market share calculation
- ✅ Average daily consumption
- ✅ Price trends
- ✅ Pie chart showing fuel distribution

**Filters:**
- From Date
- To Date
- Petrol Pump
- Fuel Type

**Key Metrics:**
- Total Liters per fuel type
- Total Sales
- Average Price per Liter
- Days Sold
- Average per Day
- Market Share %

**Use Case:**
Inventory planning, demand forecasting, pricing strategy, understanding customer preferences.

---

## 6. Pump Performance Comparison

**Purpose:** Compare performance across multiple petrol pumps

**Base DocType:** Petrol Pump

**Features:**
- ✅ Multi-pump comparison
- ✅ Profitability analysis
- ✅ Operating efficiency
- ✅ Variance tracking per pump
- ✅ Comparative bar charts

**Filters:**
- From Date
- To Date

**Key Metrics:**
- Total Liters
- Total Sales
- Total Profit
- Profit Margin %
- Average Daily Sales
- Cash Variance
- Operating Days

**Use Case:**
Multi-branch management, identifying best/worst performers, resource allocation, benchmarking.

---

## 7. Shift Profitability Analysis

**Purpose:** Analyze performance by shift (Morning/Evening/Night)

**Base DocType:** Shift Reading

**Features:**
- ✅ Shift-wise sales tracking
- ✅ Performance comparison
- ✅ Average per shift calculation
- ✅ Visual comparison chart

**Filters:**
- From Date
- To Date
- Petrol Pump
- Shift

**Key Metrics:**
- Total Liters per shift
- Total Sales per shift
- Average per Shift
- Number of Shifts worked

**Use Case:**
Shift scheduling, staff allocation, peak hour identification, shift performance evaluation.

---

## 8. Tank Utilization Report

**Purpose:** Monitor tank capacity and stock levels

**Base DocType:** Fuel Tank

**Features:**
- ✅ Current stock levels
- ✅ Capacity utilization
- ✅ Available space calculation
- ✅ Status indicators
- ✅ Utilization percentage chart

**Filters:**
- Petrol Pump
- Fuel Type

**Key Metrics:**
- Tank Capacity (liters)
- Current Stock (liters)
- Available Space (liters)
- Utilization %
- Status

**Status Categories:**
- **Full:** ≥ 90% utilized
- **Good:** 50% - 89% utilized
- **Low:** 25% - 49% utilized
- **Critical:** < 25% utilized

**Use Case:**
Refill planning, capacity optimization, preventing stockouts, managing supplier deliveries.

---

## 9. Profit Analysis Report

**Purpose:** Detailed profitability analysis by fuel type

**Base DocType:** Day Closing

**Features:**
- ✅ Revenue vs COGS analysis
- ✅ Gross profit calculation
- ✅ Profit margins by fuel type
- ✅ Profit per liter
- ✅ Summary cards (Revenue, Profit, Margin%)
- ✅ Comparative bar charts

**Filters:**
- From Date
- To Date
- Petrol Pump
- Fuel Type

**Key Metrics:**
- Liters Sold
- Revenue
- COGS (Cost of Goods Sold)
- Gross Profit
- Profit Margin %
- Profit per Liter

**Use Case:**
Financial analysis, pricing decisions, cost control, profitability optimization.

---

## 10. Monthly Summary Report

**Purpose:** Monthly performance overview and trends

**Base DocType:** Day Closing

**Features:**
- ✅ Month-wise aggregation
- ✅ Trend analysis
- ✅ Average daily sales
- ✅ Operating days tracking
- ✅ Monthly trend chart (last 12 months)
- ✅ Summary cards (Total Sales, Liters, Days)

**Filters:**
- From Date
- To Date
- Petrol Pump

**Key Metrics:**
- Total Liters (monthly)
- Total Sales (monthly)
- Cash Collected
- Credit Sales
- Cash Variance
- Operating Days
- Average Daily Sales

**Use Case:**
Month-end reviews, year-over-year comparisons, seasonal trend analysis, board reporting.

---

## 11. Shift Consumption Summary

**Purpose:** Basic shift-wise consumption tracking *(Existing Report)*

**Base DocType:** Shift Reading

**Features:**
- ✅ Date-wise shift summary
- ✅ Total liters and sales per shift

**Filters:**
- From Date
- To Date
- Petrol Pump

**Key Metrics:**
- Date
- Shift
- Total Liters
- Total Sales

**Use Case:**
Quick shift performance review.

---

## 📊 Report Categories

### 🎯 Operational Reports (Daily Use)
1. Daily Sales Summary
2. Cash Reconciliation Report
3. Stock Variance Analysis

### 📈 Performance Reports (Weekly/Monthly)
4. Nozzle Performance
5. Shift Profitability Analysis
6. Pump Performance Comparison

### 💰 Financial Reports (Management)
7. Profit Analysis Report
8. Monthly Summary Report

### 📦 Inventory Reports
9. Fuel Consumption Trends
10. Tank Utilization Report

---

## 🔍 How to Access Reports

**Navigate to:**
```
Petrol Pump V2 → Reports → [Select Report Name]
```

**Or via ERPNext:**
```
Home → Reports → Petrol Pump V2 → [Select Report]
```

---

## 📥 Export Options

All reports support:
- ✅ **Excel Export** - For further analysis
- ✅ **PDF Export** - For printing/sharing
- ✅ **Print** - Direct printing
- ✅ **Email** - Share via email

**To Export:**
1. Run the report with desired filters
2. Click "Menu" (three dots)
3. Select export format

---

## 🎨 Chart Types

Reports include various visualizations:
- **Line Charts:** Trends over time (Daily Sales, Stock Variance)
- **Bar Charts:** Comparisons (Nozzle Performance, Pump Comparison)
- **Pie Charts:** Distribution (Fuel Consumption)
- **Percentage Charts:** Utilization (Tank Utilization)

---

## 🔧 Report Features

### Common Features:
- ✅ **Totals Row:** Automatic calculation of column totals
- ✅ **Dynamic Filters:** Date ranges, pump selection
- ✅ **Real-time Data:** Always shows latest information
- ✅ **Color Coding:** Status indicators for quick insights
- ✅ **Sorting:** Click column headers to sort
- ✅ **Search:** Quick find within results

### Advanced Features:
- ✅ **Summary Cards:** Key metrics at a glance
- ✅ **Visual Charts:** Graphical representation
- ✅ **Drill-down:** Click to see details (where applicable)
- ✅ **Percentage Calculations:** Automatic variance %
- ✅ **Multi-currency:** Supports PKR, USD, etc.

---

## 💡 Best Practices

### Daily Routine:
1. **Morning:** Check Tank Utilization Report
2. **Evening:** Run Daily Sales Summary after Day Closing
3. **Daily:** Review Cash Reconciliation Report

### Weekly Routine:
1. **Monday:** Check Stock Variance Analysis (weekly)
2. **Friday:** Review Nozzle Performance
3. **Weekly:** Analyze Shift Profitability

### Monthly Routine:
1. **Month End:** Run Monthly Summary Report
2. **Month End:** Generate Profit Analysis Report
3. **Month Start:** Review Pump Performance Comparison

---

## 🚀 Coming Soon

Future reports planned:
- **Customer Analysis** (with credit customer tracking)
- **Price Change Impact**
- **Supplier Performance**
- **Employee Performance Dashboard**
- **Predictive Analytics** (demand forecasting)

---

## 📞 Support

**Issues with Reports?**
- Check filters are correctly set
- Ensure data exists for selected date range
- Verify document submission status
- Contact system administrator

**Report Requests:**
- Open an issue on GitHub
- Email: support@yourcompany.com
- Forum: Frappe Community

---

## 📝 Notes

- All reports require proper Day Closing submission
- Reports show submitted documents only (docstatus = 1)
- Canceled documents are excluded
- Date ranges are inclusive
- Currency values in company's default currency
- Liters shown with 2 decimal precision

---

**Report Suite Version:** 2.0  
**Last Updated:** 2025-01-27  
**Total Reports:** 11

---

**Built with ❤️ for the Petrol Pump Industry**

