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
			"fieldname": "employee",
			"label": _("Accountant"),
			"fieldtype": "Link",
			"options": "Employee",
			"width": 130
		},
		{
			"fieldname": "total_sales",
			"label": _("Total Sales"),
			"fieldtype": "Currency",
			"width": 120
		},
		{
			"fieldname": "cash_amount",
			"label": _("Cash Collected"),
			"fieldtype": "Currency",
			"width": 130
		},
		{
			"fieldname": "card_amount",
			"label": _("Card Amount"),
			"fieldtype": "Currency",
			"width": 120
		},
		{
			"fieldname": "credit_amount",
			"label": _("Credit Sales"),
			"fieldtype": "Currency",
			"width": 120
		},
		{
			"fieldname": "total_payments_received",
			"label": _("Total Received"),
			"fieldtype": "Currency",
			"width": 130
		},
		{
			"fieldname": "expected_collection",
			"label": _("Expected"),
			"fieldtype": "Currency",
			"width": 120
		},
		{
			"fieldname": "cash_variance",
			"label": _("Variance"),
			"fieldtype": "Currency",
			"width": 110
		},
		{
			"fieldname": "variance_pct",
			"label": _("Variance %"),
			"fieldtype": "Percent",
			"width": 100
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
			dc.reading_date,
			dc.petrol_pump,
			dc.employee,
			dc.total_sales,
			dc.cash_amount,
			dc.card_amount,
			dc.credit_amount,
			dc.total_payments_received,
			dc.expected_collection,
			dc.cash_variance
		FROM `tabDay Closing` dc
		WHERE dc.docstatus = 1
		{conditions}
		ORDER BY dc.reading_date DESC, dc.petrol_pump
	""", filters, as_dict=1)
	
	# Calculate variance percentage and status
	for row in data:
		expected = flt(row.expected_collection)
		variance = flt(row.cash_variance)
		
		# Variance percentage
		if expected:
			row['variance_pct'] = (variance / expected) * 100
		else:
			row['variance_pct'] = 0
		
		# Status
		abs_variance = abs(variance)
		if abs_variance == 0:
			row['status'] = "Perfect"
		elif abs_variance < 100:
			row['status'] = "Minor"
		elif abs_variance < 500:
			row['status'] = "Alert"
		else:
			row['status'] = "Critical"
	
	return data

def get_conditions(filters):
	conditions = []
	
	if filters.get("from_date"):
		conditions.append("dc.reading_date >= %(from_date)s")
	
	if filters.get("to_date"):
		conditions.append("dc.reading_date <= %(to_date)s")
	
	if filters.get("petrol_pump"):
		conditions.append("dc.petrol_pump = %(petrol_pump)s")
	
	if filters.get("employee"):
		conditions.append("dc.employee = %(employee)s")
	
	return " AND " + " AND ".join(conditions) if conditions else ""

def get_chart_data(data):
	if not data:
		return None
	
	# Variance trend
	dates = []
	variances = []
	
	for row in data:
		dates.append(str(row.reading_date))
		variances.append(flt(row.cash_variance))
	
	return {
		"data": {
			"labels": dates[-30:],
			"datasets": [
				{
					"name": "Cash Variance",
					"values": variances[-30:]
				}
			]
		},
		"type": "bar",
		"colors": ["#ffc107"]
	}

def get_summary(data):
	if not data:
		return []
	
	total_variance = sum(flt(row.cash_variance) for row in data)
	perfect_days = len([row for row in data if flt(row.cash_variance) == 0])
	critical_days = len([row for row in data if abs(flt(row.cash_variance)) > 500])
	
	return [
		{
			"value": total_variance,
			"indicator": "Red" if total_variance < 0 else "Green",
			"label": "Total Variance",
			"datatype": "Currency"
		},
		{
			"value": perfect_days,
			"indicator": "Green",
			"label": "Perfect Days",
			"datatype": "Int"
		},
		{
			"value": critical_days,
			"indicator": "Red" if critical_days > 0 else "Green",
			"label": "Critical Days",
			"datatype": "Int"
		}
	]

