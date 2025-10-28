# Copyright (c) 2025, Atiq and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.utils import flt, add_days, getdate

def execute(filters=None):
	filters = filters or {}
	columns = get_columns()
	data = get_data(filters)
	chart = get_chart_data(data)
	
	return columns, data, None, chart

def get_columns():
	return [
		{
			"fieldname": "fuel_type",
			"label": _("Fuel Type"),
			"fieldtype": "Link",
			"options": "Item",
			"width": 150
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
			"width": 130
		},
		{
			"fieldname": "avg_price",
			"label": _("Avg Price/L"),
			"fieldtype": "Currency",
			"width": 120
		},
		{
			"fieldname": "days_sold",
			"label": _("Days Sold"),
			"fieldtype": "Int",
			"width": 100
		},
		{
			"fieldname": "avg_per_day",
			"label": _("Avg/Day (L)"),
			"fieldtype": "Float",
			"width": 120,
			"precision": 2
		},
		{
			"fieldname": "market_share",
			"label": _("Share %"),
			"fieldtype": "Percent",
			"width": 100
		}
	]

def get_data(filters):
	conditions = get_conditions(filters)
	
	data = frappe.db.sql(f"""
		SELECT
			nrd.fuel_type,
			dc.petrol_pump,
			SUM(nrd.dispensed_liters) as total_liters,
			SUM(nrd.amount) as total_sales,
			COUNT(DISTINCT dc.reading_date) as days_sold
		FROM `tabDay Closing` dc
		INNER JOIN `tabNozzle Reading Detail` nrd ON nrd.parent = dc.name
		WHERE dc.docstatus = 1
		{conditions}
		GROUP BY nrd.fuel_type, dc.petrol_pump
		ORDER BY total_liters DESC
	""", filters, as_dict=1)
	
	# Calculate metrics
	total_liters_all = sum(flt(row.total_liters) for row in data)
	
	for row in data:
		total_liters = flt(row.total_liters)
		total_sales = flt(row.total_sales)
		days_sold = flt(row.days_sold)
		
		# Average price per liter
		if total_liters:
			row['avg_price'] = total_sales / total_liters
		else:
			row['avg_price'] = 0
		
		# Average per day
		if days_sold:
			row['avg_per_day'] = total_liters / days_sold
		else:
			row['avg_per_day'] = 0
		
		# Market share
		if total_liters_all:
			row['market_share'] = (total_liters / total_liters_all) * 100
		else:
			row['market_share'] = 0
	
	return data

def get_conditions(filters):
	conditions = []
	
	if filters.get("from_date"):
		conditions.append("dc.reading_date >= %(from_date)s")
	
	if filters.get("to_date"):
		conditions.append("dc.reading_date <= %(to_date)s")
	
	if filters.get("petrol_pump"):
		conditions.append("dc.petrol_pump = %(petrol_pump)s")
	
	if filters.get("fuel_type"):
		conditions.append("nrd.fuel_type = %(fuel_type)s")
	
	return " AND " + " AND ".join(conditions) if conditions else ""

def get_chart_data(data):
	if not data:
		return None
	
	# Pie chart for fuel type distribution
	labels = []
	values = []
	
	for row in data:
		if row.fuel_type not in labels:
			labels.append(row.fuel_type)
			values.append(flt(row.total_liters))
		else:
			idx = labels.index(row.fuel_type)
			values[idx] += flt(row.total_liters)
	
	return {
		"data": {
			"labels": labels,
			"datasets": [
				{
					"name": "Fuel Distribution",
					"values": values
				}
			]
		},
		"type": "pie",
		"colors": ["#28a745", "#007bff", "#ffc107", "#dc3545", "#17a2b8"]
	}

