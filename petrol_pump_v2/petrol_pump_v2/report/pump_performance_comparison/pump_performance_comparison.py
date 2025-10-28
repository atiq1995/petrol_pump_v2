# Copyright (c) 2025, Atiq and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.utils import flt

def execute(filters=None):
	filters = filters or {}
	columns = get_columns()
	data = get_data(filters)
	chart = get_chart_data(data)
	
	return columns, data, None, chart

def get_columns():
	return [
		{
			"fieldname": "petrol_pump",
			"label": _("Petrol Pump"),
			"fieldtype": "Link",
			"options": "Petrol Pump",
			"width": 180
		},
		{
			"fieldname": "total_liters",
			"label": _("Total Liters"),
			"fieldtype": "Float",
			"width": 130,
			"precision": 2
		},
		{
			"fieldname": "total_sales",
			"label": _("Total Sales"),
			"fieldtype": "Currency",
			"width": 140
		},
		{
			"fieldname": "total_profit",
			"label": _("Total Profit"),
			"fieldtype": "Currency",
			"width": 140
		},
		{
			"fieldname": "profit_margin",
			"label": _("Profit %"),
			"fieldtype": "Percent",
			"width": 100
		},
		{
			"fieldname": "avg_daily_sales",
			"label": _("Avg Daily Sales"),
			"fieldtype": "Currency",
			"width": 140
		},
		{
			"fieldname": "cash_variance",
			"label": _("Total Variance"),
			"fieldtype": "Currency",
			"width": 130
		},
		{
			"fieldname": "operating_days",
			"label": _("Operating Days"),
			"fieldtype": "Int",
			"width": 120
		}
	]

def get_data(filters):
	conditions = get_conditions(filters)
	
	data = frappe.db.sql(f"""
		SELECT
			dc.petrol_pump,
			SUM(dc.total_liters) as total_liters,
			SUM(dc.total_sales) as total_sales,
			SUM(dc.cash_variance) as cash_variance,
			COUNT(dc.name) as operating_days,
			SUM(
				COALESCE((SELECT SUM(se_item.amount)
				 FROM `tabStock Entry` se
				 INNER JOIN `tabStock Entry Detail` se_item ON se_item.parent = se.name
				 WHERE se.name = dc.stock_entry_ref AND se.docstatus = 1), 0)
			) as total_cogs
		FROM `tabDay Closing` dc
		WHERE dc.docstatus = 1
		{conditions}
		GROUP BY dc.petrol_pump
		ORDER BY total_sales DESC
	""", filters, as_dict=1)
	
	# Calculate metrics
	for row in data:
		total_sales = flt(row.total_sales)
		total_cogs = flt(row.total_cogs)
		operating_days = flt(row.operating_days)
		
		# Profit
		row['total_profit'] = total_sales - total_cogs
		
		# Profit margin
		if total_sales:
			row['profit_margin'] = (row['total_profit'] / total_sales) * 100
		else:
			row['profit_margin'] = 0
		
		# Average daily sales
		if operating_days:
			row['avg_daily_sales'] = total_sales / operating_days
		else:
			row['avg_daily_sales'] = 0
	
	return data

def get_conditions(filters):
	conditions = []
	
	if filters.get("from_date"):
		conditions.append("dc.reading_date >= %(from_date)s")
	
	if filters.get("to_date"):
		conditions.append("dc.reading_date <= %(to_date)s")
	
	return " AND " + " AND ".join(conditions) if conditions else ""

def get_chart_data(data):
	if not data:
		return None
	
	labels = [row.petrol_pump for row in data]
	sales = [flt(row.total_sales) for row in data]
	profit = [flt(row.total_profit) for row in data]
	
	return {
		"data": {
			"labels": labels,
			"datasets": [
				{
					"name": "Total Sales",
					"values": sales
				},
				{
					"name": "Total Profit",
					"values": profit
				}
			]
		},
		"type": "bar",
		"colors": ["#28a745", "#007bff"]
	}

