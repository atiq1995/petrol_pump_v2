# Copyright (c) 2026, Atiq and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.utils import flt, getdate, fmt_money


def execute(filters=None):
	filters = filters or {}
	columns = get_columns()
	data = get_data(filters)
	chart = get_chart_data(data, filters)

	return columns, data, None, chart


def get_columns():
	return [
		{
			"fieldname": "petrol_pump",
			"label": _("Petrol Pump"),
			"fieldtype": "Link",
			"options": "Petrol Pump",
			"width": 160
		},
		{
			"fieldname": "fuel_type",
			"label": _("Fuel Type"),
			"fieldtype": "Link",
			"options": "Fuel Type",
			"width": 130
		},
		{
			"fieldname": "fuel_type_name",
			"label": _("Fuel Name"),
			"fieldtype": "Data",
			"width": 130
		},
		{
			"fieldname": "price_per_liter",
			"label": _("Price Per Liter"),
			"fieldtype": "Currency",
			"width": 130
		},
		{
			"fieldname": "effective_from",
			"label": _("Effective From"),
			"fieldtype": "Datetime",
			"width": 170
		},
		{
			"fieldname": "is_active",
			"label": _("Active"),
			"fieldtype": "Check",
			"width": 70
		},
		{
			"fieldname": "previous_price",
			"label": _("Previous Price"),
			"fieldtype": "Currency",
			"width": 130
		},
		{
			"fieldname": "price_change",
			"label": _("Change"),
			"fieldtype": "Currency",
			"width": 110
		},
		{
			"fieldname": "change_percent",
			"label": _("Change %"),
			"fieldtype": "Percent",
			"width": 100
		},
		{
			"fieldname": "fuel_price_name",
			"label": _("Fuel Price ID"),
			"fieldtype": "Link",
			"options": "Fuel Price",
			"width": 140
		}
	]


def get_data(filters):
	conditions = get_conditions(filters)

	data = frappe.db.sql(f"""
		SELECT
			fp.name as fuel_price_name,
			fp.petrol_pump,
			fpd.fuel_type,
			fpd.price_per_liter,
			fp.effective_from,
			fp.is_active
		FROM `tabFuel Price Detail` fpd
		JOIN `tabFuel Price` fp ON fpd.parent = fp.name
		WHERE 1=1
		{conditions}
		ORDER BY fp.petrol_pump, fpd.fuel_type, fp.effective_from DESC
	""", filters, as_dict=1)

	# Resolve fuel type names and calculate price changes
	result = []
	# Group by pump + fuel_type to find previous prices
	prev_price_map = {}

	for row in data:
		# Resolve fuel type name
		row["fuel_type_name"] = frappe.db.get_value(
			"Fuel Type", row["fuel_type"], "fuel_type_name"
		) or row["fuel_type"]

		# Build key for tracking price changes
		key = f"{row['petrol_pump']}::{row['fuel_type']}"

		if key in prev_price_map:
			# This is an older entry; the one before it was the "next" chronologically
			prev_price_map[key]["previous_price"] = flt(row["price_per_liter"])
			prev_price = flt(row["price_per_liter"])
			curr_price = flt(prev_price_map[key]["price_per_liter"])
			prev_price_map[key]["price_change"] = curr_price - prev_price
			if prev_price > 0:
				prev_price_map[key]["change_percent"] = (
					(curr_price - prev_price) / prev_price
				) * 100
			else:
				prev_price_map[key]["change_percent"] = 0

		# Set defaults
		row["previous_price"] = 0
		row["price_change"] = 0
		row["change_percent"] = 0

		prev_price_map[key] = row
		result.append(row)

	return result


def get_conditions(filters):
	conditions = []

	if filters.get("petrol_pump"):
		conditions.append("fp.petrol_pump = %(petrol_pump)s")

	if filters.get("fuel_type"):
		conditions.append("fpd.fuel_type = %(fuel_type)s")

	if filters.get("from_date"):
		conditions.append("fp.effective_from >= %(from_date)s")

	if filters.get("to_date"):
		conditions.append("fp.effective_from <= %(to_date)s")

	if filters.get("is_active"):
		conditions.append("fp.is_active = 1")

	return " AND " + " AND ".join(conditions) if conditions else ""


def get_chart_data(data, filters):
	if not data:
		return None

	# Group by fuel type for chart lines
	fuel_types = {}
	dates = []

	for row in data:
		ft = row.get("fuel_type_name") or row.get("fuel_type")
		if ft not in fuel_types:
			fuel_types[ft] = {}

		date_str = str(row["effective_from"])[:10]
		fuel_types[ft][date_str] = flt(row["price_per_liter"])

		if date_str not in dates:
			dates.append(date_str)

	dates.sort()

	# Build datasets - fill forward prices for dates where a fuel type has no entry
	datasets = []
	colors = ["#e74c3c", "#3498db", "#2ecc71", "#f39c12", "#9b59b6", "#1abc9c"]

	for idx, (ft, prices) in enumerate(fuel_types.items()):
		values = []
		last_price = 0
		for d in dates:
			if d in prices:
				last_price = prices[d]
			values.append(last_price)

		datasets.append({
			"name": ft,
			"values": values
		})

	return {
		"data": {
			"labels": dates[-50:],
			"datasets": [
				{
					"name": ds["name"],
					"values": ds["values"][-50:]
				}
				for ds in datasets
			]
		},
		"type": "line",
		"colors": colors[:len(datasets)],
		"axisOptions": {
			"xIsSeries": 1
		}
	}
