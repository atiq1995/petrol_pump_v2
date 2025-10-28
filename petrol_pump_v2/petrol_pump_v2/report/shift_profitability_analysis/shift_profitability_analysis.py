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
			"fieldname": "shift",
			"label": _("Shift"),
			"fieldtype": "Link",
			"options": "Shift",
			"width": 130
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
			"fieldname": "avg_per_shift",
			"label": _("Avg/Shift"),
			"fieldtype": "Currency",
			"width": 120
		},
		{
			"fieldname": "shifts_worked",
			"label": _("# Shifts"),
			"fieldtype": "Int",
			"width": 90
		}
	]

def get_data(filters):
	conditions = get_conditions(filters)
	
	data = frappe.db.sql(f"""
		SELECT
			sr.shift,
			sr.petrol_pump,
			SUM(sr.total_liters) as total_liters,
			SUM(sr.total_sales) as total_sales,
			COUNT(sr.name) as shifts_worked
		FROM `tabShift Reading` sr
		WHERE sr.docstatus = 1
		{conditions}
		GROUP BY sr.shift, sr.petrol_pump
		ORDER BY total_sales DESC
	""", filters, as_dict=1)
	
	# Calculate averages
	for row in data:
		shifts_worked = flt(row.shifts_worked)
		if shifts_worked:
			row['avg_per_shift'] = flt(row.total_sales) / shifts_worked
		else:
			row['avg_per_shift'] = 0
	
	return data

def get_conditions(filters):
	conditions = []
	
	if filters.get("from_date"):
		conditions.append("sr.reading_date >= %(from_date)s")
	
	if filters.get("to_date"):
		conditions.append("sr.reading_date <= %(to_date)s")
	
	if filters.get("petrol_pump"):
		conditions.append("sr.petrol_pump = %(petrol_pump)s")
	
	if filters.get("shift"):
		conditions.append("sr.shift = %(shift)s")
	
	return " AND " + " AND ".join(conditions) if conditions else ""

def get_chart_data(data):
	if not data:
		return None
	
	labels = []
	values = []
	
	for row in data:
		if row.shift not in labels:
			labels.append(row.shift)
			values.append(flt(row.total_sales))
		else:
			idx = labels.index(row.shift)
			values[idx] += flt(row.total_sales)
	
	return {
		"data": {
			"labels": labels,
			"datasets": [
				{
					"name": "Sales by Shift",
					"values": values
				}
			]
		},
		"type": "bar",
		"colors": ["#007bff"]
	}

