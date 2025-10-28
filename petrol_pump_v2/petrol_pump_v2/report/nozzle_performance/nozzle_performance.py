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
			"width": 150
		},
		{
			"fieldname": "dispenser",
			"label": _("Dispenser"),
			"fieldtype": "Link",
			"options": "Dispenser",
			"width": 130
		},
		{
			"fieldname": "nozzle_number",
			"label": _("Nozzle"),
			"fieldtype": "Data",
			"width": 80
		},
		{
			"fieldname": "fuel_type",
			"label": _("Fuel Type"),
			"fieldtype": "Link",
			"options": "Item",
			"width": 130
		},
		{
			"fieldname": "total_liters",
			"label": _("Total Liters"),
			"fieldtype": "Float",
			"width": 120,
			"precision": 2
		},
		{
			"fieldname": "total_amount",
			"label": _("Total Sales"),
			"fieldtype": "Currency",
			"width": 130
		},
		{
			"fieldname": "avg_per_day",
			"label": _("Avg/Day (L)"),
			"fieldtype": "Float",
			"width": 110,
			"precision": 2
		},
		{
			"fieldname": "transactions",
			"label": _("# of Days"),
			"fieldtype": "Int",
			"width": 100
		}
	]

def get_data(filters):
	conditions = get_conditions(filters)
	
	data = frappe.db.sql(f"""
		SELECT
			dc.petrol_pump,
			nrd.dispenser,
			nrd.nozzle_number,
			nrd.fuel_type,
			SUM(nrd.dispensed_liters) as total_liters,
			SUM(nrd.amount) as total_amount,
			COUNT(DISTINCT dc.name) as transactions
		FROM `tabDay Closing` dc
		INNER JOIN `tabNozzle Reading Detail` nrd ON nrd.parent = dc.name
		WHERE dc.docstatus = 1
		{conditions}
		GROUP BY dc.petrol_pump, nrd.dispenser, nrd.nozzle_number, nrd.fuel_type
		ORDER BY dc.petrol_pump, nrd.dispenser, nrd.nozzle_number
	""", filters, as_dict=1)
	
	# Calculate averages
	for row in data:
		if row.transactions:
			row['avg_per_day'] = flt(row.total_liters) / flt(row.transactions)
		else:
			row['avg_per_day'] = 0
	
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
	
	# Top 10 nozzles by sales
	sorted_data = sorted(data, key=lambda x: flt(x.total_amount), reverse=True)[:10]
	
	labels = [f"{row.dispenser}-N{row.nozzle_number}" for row in sorted_data]
	values = [flt(row.total_amount) for row in sorted_data]
	
	return {
		"data": {
			"labels": labels,
			"datasets": [
				{
					"name": "Sales Amount",
					"values": values
				}
			]
		},
		"type": "bar",
		"colors": ["#28a745"]
	}

