import frappe


def execute(filters=None):
	filters = filters or {}
	columns = [
		{"label": "Date", "fieldname": "reading_date", "fieldtype": "Date", "width": 100},
		{"label": "Petrol Pump", "fieldname": "petrol_pump", "fieldtype": "Link", "options": "Petrol Pump", "width": 160},
		{"label": "Shift", "fieldname": "shift", "fieldtype": "Link", "options": "Shift", "width": 140},
		{"label": "Total Liters", "fieldname": "total_liters", "fieldtype": "Float", "width": 120},
		{"label": "Total Sales", "fieldname": "total_sales", "fieldtype": "Currency", "width": 120},
	]

	conditions = []
	values = {}
	if filters.get("from_date"):
		conditions.append("sr.reading_date >= %(from_date)s")
		values["from_date"] = filters["from_date"]
	if filters.get("to_date"):
		conditions.append("sr.reading_date <= %(to_date)s")
		values["to_date"] = filters["to_date"]
	if filters.get("petrol_pump"):
		conditions.append("sr.petrol_pump = %(petrol_pump)s")
		values["petrol_pump"] = filters["petrol_pump"]

	where = (" where " + " and ".join(conditions)) if conditions else ""
	data = frappe.db.sql(
		f"""
			select
				sr.reading_date, sr.petrol_pump, sr.shift, sr.total_liters, sr.total_sales
			from `tabShift Reading` sr
			{where}
			order by sr.reading_date desc, sr.petrol_pump
		""",
		values,
		as_dict=True,
	)
	return columns, data
