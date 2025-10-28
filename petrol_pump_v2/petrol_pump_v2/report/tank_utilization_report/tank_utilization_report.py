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
			"fieldname": "tank_name",
			"label": _("Tank Name"),
			"fieldtype": "Link",
			"options": "Fuel Tank",
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
			"fieldname": "fuel_type",
			"label": _("Fuel Type"),
			"fieldtype": "Link",
			"options": "Item",
			"width": 130
		},
		{
			"fieldname": "capacity",
			"label": _("Capacity (L)"),
			"fieldtype": "Float",
			"width": 120,
			"precision": 2
		},
		{
			"fieldname": "current_stock",
			"label": _("Current Stock (L)"),
			"fieldtype": "Float",
			"width": 140,
			"precision": 2
		},
		{
			"fieldname": "available_space",
			"label": _("Available Space (L)"),
			"fieldtype": "Float",
			"width": 150,
			"precision": 2
		},
		{
			"fieldname": "utilization_pct",
			"label": _("Utilization %"),
			"fieldtype": "Percent",
			"width": 120
		},
		{
			"fieldname": "status",
			"label": _("Status"),
			"fieldtype": "Data",
			"width": 100
		}
	]

def get_data(filters):
	conditions = get_conditions(filters)
	
	data = frappe.db.sql(f"""
		SELECT
			ft.name as tank_name,
			ft.petrol_pump,
			ft.fuel_type,
			ft.capacity,
			ft.current_stock
		FROM `tabFuel Tank` ft
		WHERE 1=1
		{conditions}
		ORDER BY ft.petrol_pump, ft.tank_name
	""", filters, as_dict=1)
	
	# Calculate metrics
	for row in data:
		capacity = flt(row.capacity)
		current_stock = flt(row.current_stock)
		
		# Available space
		row['available_space'] = capacity - current_stock
		
		# Utilization percentage
		if capacity:
			row['utilization_pct'] = (current_stock / capacity) * 100
		else:
			row['utilization_pct'] = 0
		
		# Status
		utilization = row['utilization_pct']
		if utilization >= 90:
			row['status'] = "Full"
		elif utilization >= 50:
			row['status'] = "Good"
		elif utilization >= 25:
			row['status'] = "Low"
		else:
			row['status'] = "Critical"
	
	return data

def get_conditions(filters):
	conditions = []
	
	if filters.get("petrol_pump"):
		conditions.append("ft.petrol_pump = %(petrol_pump)s")
	
	if filters.get("fuel_type"):
		conditions.append("ft.fuel_type = %(fuel_type)s")
	
	return " AND " + " AND ".join(conditions) if conditions else ""

def get_chart_data(data):
	if not data:
		return None
	
	labels = [row.tank_name for row in data]
	values = [flt(row.utilization_pct) for row in data]
	
	return {
		"data": {
			"labels": labels,
			"datasets": [
				{
					"name": "Utilization %",
					"values": values
				}
			]
		},
		"type": "percentage",
		"colors": ["#28a745"]
	}

