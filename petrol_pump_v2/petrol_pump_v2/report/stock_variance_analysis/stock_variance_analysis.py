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
			"fieldname": "fuel_tank",
			"label": _("Tank"),
			"fieldtype": "Link",
			"options": "Fuel Tank",
			"width": 130
		},
		{
			"fieldname": "fuel_type",
			"label": _("Fuel Type"),
			"fieldtype": "Data",
			"width": 120
		},
		{
			"fieldname": "system_stock",
			"label": _("System Stock (L)"),
			"fieldtype": "Float",
			"width": 130,
			"precision": 2
		},
		{
			"fieldname": "measured_stock",
			"label": _("Physical Stock (L)"),
			"fieldtype": "Float",
			"width": 140,
			"precision": 2
		},
		{
			"fieldname": "variance",
			"label": _("Variance (L)"),
			"fieldtype": "Float",
			"width": 120,
			"precision": 2
		},
		{
			"fieldname": "variance_pct",
			"label": _("Variance %"),
			"fieldtype": "Percent",
			"width": 110
		},
		{
			"fieldname": "variance_value",
			"label": _("Value Impact"),
			"fieldtype": "Currency",
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
			dr.reading_date,
			dr.petrol_pump,
			drd.fuel_tank,
			ft.fuel_type,
			drd.system_stock,
			drd.measured_stock,
			drd.variance,
			drd.temperature,
			drd.water_level
		FROM `tabDip Reading` dr
		INNER JOIN `tabDip Reading Detail` drd ON drd.parent = dr.name
		LEFT JOIN `tabFuel Tank` ft ON ft.name = drd.fuel_tank
		WHERE dr.docstatus = 1
		{conditions}
		ORDER BY dr.reading_date DESC, dr.petrol_pump
	""", filters, as_dict=1)
	
	# Calculate variance percentage and value
	for row in data:
		system_stock = flt(row.system_stock)
		variance = flt(row.variance)
		
		# Variance percentage
		if system_stock:
			row['variance_pct'] = (variance / system_stock) * 100
		else:
			row['variance_pct'] = 0
		
		# Get valuation rate to calculate value impact
		valuation_rate = frappe.db.get_value(
			"Stock Ledger Entry",
			{
				"item_code": row.fuel_type,
				"is_cancelled": 0
			},
			"valuation_rate",
			order_by="posting_date desc, posting_time desc"
		) or 0
		
		row['variance_value'] = variance * flt(valuation_rate)
		
		# Status based on variance
		abs_variance_pct = abs(row['variance_pct'])
		if abs_variance_pct == 0:
			row['status'] = "Perfect"
		elif abs_variance_pct < 0.5:
			row['status'] = "Normal"
		elif abs_variance_pct < 1:
			row['status'] = "Alert"
		else:
			row['status'] = "Critical"
	
	return data

def get_conditions(filters):
	conditions = []
	
	if filters.get("from_date"):
		conditions.append("dr.reading_date >= %(from_date)s")
	
	if filters.get("to_date"):
		conditions.append("dr.reading_date <= %(to_date)s")
	
	if filters.get("petrol_pump"):
		conditions.append("dr.petrol_pump = %(petrol_pump)s")
	
	if filters.get("fuel_tank"):
		conditions.append("drd.fuel_tank = %(fuel_tank)s")
	
	return " AND " + " AND ".join(conditions) if conditions else ""

def get_chart_data(data):
	if not data:
		return None
	
	# Variance trend over time
	dates = []
	variances = []
	
	for row in data:
		date_str = str(row.reading_date)
		if date_str not in dates:
			dates.append(date_str)
			variances.append(flt(row.variance))
		else:
			idx = dates.index(date_str)
			variances[idx] += flt(row.variance)
	
	return {
		"data": {
			"labels": dates[-30:],
			"datasets": [
				{
					"name": "Variance (Liters)",
					"values": variances[-30:]
				}
			]
		},
		"type": "line",
		"colors": ["#dc3545"],
		"axisOptions": {
			"xIsSeries": 1
		}
	}

