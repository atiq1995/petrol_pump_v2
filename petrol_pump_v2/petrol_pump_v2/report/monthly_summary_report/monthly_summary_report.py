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
	summary = get_summary(data)
	
	return columns, data, None, chart, summary

def get_columns():
	return [
		{
			"fieldname": "month",
			"label": _("Month"),
			"fieldtype": "Data",
			"width": 120
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
			"fieldname": "cash_collected",
			"label": _("Cash Collected"),
			"fieldtype": "Currency",
			"width": 140
		},
		{
			"fieldname": "credit_sales",
			"label": _("Credit Sales"),
			"fieldtype": "Currency",
			"width": 130
		},
		{
			"fieldname": "cash_variance",
			"label": _("Total Variance"),
			"fieldtype": "Currency",
			"width": 130
		},
		{
			"fieldname": "operating_days",
			"label": _("Days"),
			"fieldtype": "Int",
			"width": 80
		},
		{
			"fieldname": "avg_daily_sales",
			"label": _("Avg/Day"),
			"fieldtype": "Currency",
			"width": 120
		}
	]

def get_data(filters):
	conditions = get_conditions(filters)
	
	data = frappe.db.sql(f"""
		SELECT
			DATE_FORMAT(dc.reading_date, '%%Y-%%m') as month,
			dc.petrol_pump,
			SUM(dc.total_liters) as total_liters,
			SUM(dc.total_sales) as total_sales,
			SUM(dc.cash_amount) as cash_collected,
			SUM(dc.credit_amount) as credit_sales,
			SUM(dc.cash_variance) as cash_variance,
			COUNT(dc.name) as operating_days
		FROM `tabDay Closing` dc
		WHERE dc.docstatus = 1
		{conditions}
		GROUP BY month, dc.petrol_pump
		ORDER BY month DESC, dc.petrol_pump
	""", filters, as_dict=1)
	
	# Calculate averages
	for row in data:
		operating_days = flt(row.operating_days)
		if operating_days:
			row['avg_daily_sales'] = flt(row.total_sales) / operating_days
		else:
			row['avg_daily_sales'] = 0
	
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
	
	months = []
	sales = []
	
	for row in data:
		if row.month not in months:
			months.append(row.month)
			sales.append(flt(row.total_sales))
		else:
			idx = months.index(row.month)
			sales[idx] += flt(row.total_sales)
	
	return {
		"data": {
			"labels": months[-12:],  # Last 12 months
			"datasets": [
				{
					"name": "Monthly Sales",
					"values": sales[-12:]
				}
			]
		},
		"type": "line",
		"colors": ["#28a745"],
		"axisOptions": {
			"xIsSeries": 1
		}
	}

def get_summary(data):
	if not data:
		return []
	
	total_sales = sum(flt(row.total_sales) for row in data)
	total_liters = sum(flt(row.total_liters) for row in data)
	total_days = sum(flt(row.operating_days) for row in data)
	
	return [
		{
			"value": total_sales,
			"indicator": "Green",
			"label": "Total Sales",
			"datatype": "Currency"
		},
		{
			"value": total_liters,
			"indicator": "Blue",
			"label": "Total Liters",
			"datatype": "Float"
		},
		{
			"value": total_days,
			"indicator": "Orange",
			"label": "Operating Days",
			"datatype": "Int"
		}
	]

