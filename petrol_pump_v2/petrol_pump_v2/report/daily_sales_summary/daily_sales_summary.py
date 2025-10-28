# Copyright (c) 2025, Atiq and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.utils import flt, getdate

def execute(filters=None):
	filters = filters or {}
	columns = get_columns()
	data = get_data(filters)
	chart = get_chart_data(data)
	
	return columns, data, None, chart

def get_columns():
	return [
		{
			"fieldname": "reading_date",
			"label": _("Date"),
			"fieldtype": "Date",
			"width": 100
		},
		{
			"fieldname": "petrol_pump",
			"label": _("Petrol Pump"),
			"fieldtype": "Link",
			"options": "Petrol Pump",
			"width": 150
		},
		{
			"fieldname": "total_liters",
			"label": _("Total Liters"),
			"fieldtype": "Float",
			"width": 120,
			"precision": 2
		},
		{
			"fieldname": "total_sales",
			"label": _("Total Sales"),
			"fieldtype": "Currency",
			"width": 130
		},
		{
			"fieldname": "cash_amount",
			"label": _("Cash"),
			"fieldtype": "Currency",
			"width": 120
		},
		{
			"fieldname": "card_amount",
			"label": _("Card/POS"),
			"fieldtype": "Currency",
			"width": 120
		},
		{
			"fieldname": "credit_amount",
			"label": _("Credit"),
			"fieldtype": "Currency",
			"width": 120
		},
		{
			"fieldname": "cash_variance",
			"label": _("Variance"),
			"fieldtype": "Currency",
			"width": 100
		},
		{
			"fieldname": "profit",
			"label": _("Estimated Profit"),
			"fieldtype": "Currency",
			"width": 130
		},
		{
			"fieldname": "profit_margin",
			"label": _("Profit %"),
			"fieldtype": "Percent",
			"width": 100
		}
	]

def get_data(filters):
	conditions = get_conditions(filters)
	
	data = frappe.db.sql(f"""
		SELECT
			dc.reading_date,
			dc.petrol_pump,
			dc.total_liters,
			dc.total_sales,
			dc.cash_amount,
			dc.card_amount,
			dc.credit_amount,
			dc.cash_variance,
			COALESCE(
				(SELECT SUM(se_item.amount)
				 FROM `tabStock Entry` se
				 INNER JOIN `tabStock Entry Detail` se_item ON se_item.parent = se.name
				 WHERE se.name = dc.stock_entry_ref AND se.docstatus = 1),
				0
			) as cost_of_goods_sold
		FROM `tabDay Closing` dc
		WHERE dc.docstatus = 1
		{conditions}
		ORDER BY dc.reading_date DESC, dc.petrol_pump
	""", filters, as_dict=1)
	
	# Calculate profit
	for row in data:
		cogs = flt(row.get('cost_of_goods_sold', 0))
		row['profit'] = flt(row.total_sales) - cogs
		if row.total_sales:
			row['profit_margin'] = (row['profit'] / row.total_sales) * 100
		else:
			row['profit_margin'] = 0
	
	return data

def get_conditions(filters):
	conditions = []
	
	if filters.get("from_date"):
		conditions.append("dc.reading_date >= %(from_date)s")
	
	if filters.get("to_date"):
		conditions.append("dc.reading_date <= %(to_date)s")
	
	if filters.get("petrol_pump"):
		conditions.append("dc.petrol_pump = %(petrol_pump)s")
	
	return " AND " + " AND ".join(conditions) if conditions else ""

def get_chart_data(data):
	if not data:
		return None
	
	# Group by date
	dates = []
	sales = []
	profit = []
	
	for row in data:
		if row.reading_date not in dates:
			dates.append(str(row.reading_date))
			sales.append(flt(row.total_sales))
			profit.append(flt(row.profit))
		else:
			idx = dates.index(str(row.reading_date))
			sales[idx] += flt(row.total_sales)
			profit[idx] += flt(row.profit)
	
	return {
		"data": {
			"labels": dates[-30:],  # Last 30 days
			"datasets": [
				{
					"name": "Total Sales",
					"values": sales[-30:]
				},
				{
					"name": "Profit",
					"values": profit[-30:]
				}
			]
		},
		"type": "line",
		"colors": ["#28a745", "#007bff"],
		"axisOptions": {
			"xIsSeries": 1
		}
	}

