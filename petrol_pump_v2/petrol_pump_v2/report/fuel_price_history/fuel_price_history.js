frappe.query_reports["Fuel Price History"] = {
	"filters": [
		{
			"fieldname": "petrol_pump",
			"label": __("Petrol Pump"),
			"fieldtype": "Link",
			"options": "Petrol Pump",
			"width": 150
		},
		{
			"fieldname": "fuel_type",
			"label": __("Fuel Type"),
			"fieldtype": "Link",
			"options": "Fuel Type",
			"width": 130
		},
		{
			"fieldname": "from_date",
			"label": __("From Date"),
			"fieldtype": "Date",
			"width": 100
		},
		{
			"fieldname": "to_date",
			"label": __("To Date"),
			"fieldtype": "Date",
			"width": 100,
			"default": frappe.datetime.get_today()
		},
		{
			"fieldname": "is_active",
			"label": __("Active Only"),
			"fieldtype": "Check",
			"default": 0
		}
	]
};
