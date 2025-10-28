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
	summary = get_summary(data)
	
	return columns, data, None, chart, summary

def get_columns():
	return [
		{
			"fieldname": "fuel_type",
			"label": _("Fuel Type"),
			"fieldtype": "Link",
			"options": "Item",
			"width": 140
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
			"label": _("Liters Sold"),
			"fieldtype": "Float",
			"width": 120,
			"precision": 2
		},
		{
			"fieldname": "total_revenue",
			"label": _("Revenue"),
			"fieldtype": "Currency",
			"width": 130
		},
		{
			"fieldname": "total_cogs",
			"label": _("COGS"),
			"fieldtype": "Currency",
			"width": 130
		},
		{
			"fieldname": "gross_profit",
			"label": _("Gross Profit"),
			"fieldtype": "Currency",
			"width": 130
		},
		{
			"fieldname": "profit_margin",
			"label": _("Margin %"),
			"fieldtype": "Percent",
			"width": 100
		},
		{
			"fieldname": "profit_per_liter",
			"label": _("Profit/L"),
			"fieldtype": "Currency",
			"width": 110
		}
	]

def get_data(filters):
	conditions = get_conditions(filters)
	
	# Get revenue data
	revenue_data = frappe.db.sql(f"""
		SELECT
			nrd.fuel_type,
			dc.petrol_pump,
			SUM(nrd.dispensed_liters) as total_liters,
			SUM(nrd.amount) as total_revenue
		FROM `tabDay Closing` dc
		INNER JOIN `tabNozzle Reading Detail` nrd ON nrd.parent = dc.name
		WHERE dc.docstatus = 1
		{conditions}
		GROUP BY nrd.fuel_type, dc.petrol_pump
	""", filters, as_dict=1)
	
	# Get COGS data from Stock Entries
	for row in revenue_data:
		cogs_query = f"""
			SELECT
				SUM(se_item.amount) as total_cogs
			FROM `tabDay Closing` dc
			INNER JOIN `tabStock Entry` se ON se.name = dc.stock_entry_ref
			INNER JOIN `tabStock Entry Detail` se_item ON se_item.parent = se.name
			INNER JOIN `tabNozzle Reading Detail` nrd ON nrd.parent = dc.name
			WHERE dc.docstatus = 1
				AND se.docstatus = 1
				AND se_item.item_code = %(fuel_type)s
				AND dc.petrol_pump = %(petrol_pump)s
				{conditions.replace("dc.", "")}
		"""
		
		cogs_result = frappe.db.sql(
			cogs_query,
			{"fuel_type": row.fuel_type, "petrol_pump": row.petrol_pump, **filters},
			as_dict=1
		)
		
		row['total_cogs'] = flt(cogs_result[0].total_cogs) if cogs_result else 0
		
		# Calculate profit metrics
		revenue = flt(row.total_revenue)
		cogs = flt(row.total_cogs)
		liters = flt(row.total_liters)
		
		row['gross_profit'] = revenue - cogs
		
		if revenue:
			row['profit_margin'] = (row['gross_profit'] / revenue) * 100
		else:
			row['profit_margin'] = 0
		
		if liters:
			row['profit_per_liter'] = row['gross_profit'] / liters
		else:
			row['profit_per_liter'] = 0
	
	return revenue_data

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
	
	labels = []
	revenue = []
	cogs = []
	profit = []
	
	for row in data:
		label = f"{row.fuel_type[:10]}"
		if label not in labels:
			labels.append(label)
			revenue.append(flt(row.total_revenue))
			cogs.append(flt(row.total_cogs))
			profit.append(flt(row.gross_profit))
		else:
			idx = labels.index(label)
			revenue[idx] += flt(row.total_revenue)
			cogs[idx] += flt(row.total_cogs)
			profit[idx] += flt(row.gross_profit)
	
	return {
		"data": {
			"labels": labels,
			"datasets": [
				{
					"name": "Revenue",
					"values": revenue
				},
				{
					"name": "COGS",
					"values": cogs
				},
				{
					"name": "Profit",
					"values": profit
				}
			]
		},
		"type": "bar",
		"colors": ["#28a745", "#dc3545", "#007bff"]
	}

def get_summary(data):
	if not data:
		return []
	
	total_revenue = sum(flt(row.total_revenue) for row in data)
	total_cogs = sum(flt(row.total_cogs) for row in data)
	total_profit = total_revenue - total_cogs
	avg_margin = (total_profit / total_revenue * 100) if total_revenue else 0
	
	return [
		{
			"value": total_revenue,
			"indicator": "Green",
			"label": "Total Revenue",
			"datatype": "Currency"
		},
		{
			"value": total_profit,
			"indicator": "Blue",
			"label": "Total Profit",
			"datatype": "Currency"
		},
		{
			"value": avg_margin,
			"indicator": "Orange",
			"label": "Avg Margin %",
			"datatype": "Percent"
		}
	]

