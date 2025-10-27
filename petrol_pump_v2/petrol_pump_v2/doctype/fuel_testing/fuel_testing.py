import frappe
from frappe.model.document import Document
from frappe.utils import flt, nowdate, get_datetime
from erpnext.stock.utils import get_stock_balance

class FuelTesting(Document):
	def before_save(self):
		self.calculate_totals()
		self.validate_stock_availability()

	def on_submit(self):
		self.create_testing_stock_entry()
	
	def on_cancel(self):
		"""Cancel linked Stock Entry"""
		self.cancel_stock_entry()

	def calculate_totals(self):
		total_liters = 0

		for detail in self.fuel_testing_details:
			total_liters += flt(detail.test_liters)

		self.total_test_liters = total_liters

	def validate_stock_availability(self):
		if not self.petrol_pump:
			return

		fuel_consumption = {}
		for detail in self.fuel_testing_details:
			if detail.test_liters > 0:
				fuel_type = detail.fuel_type
				liters = detail.test_liters
				fuel_consumption[fuel_type] = fuel_consumption.get(fuel_type, 0) + liters

		for fuel_type, liters_to_test in fuel_consumption.items():
			tank = frappe.get_all("Fuel Tank",
				filters={"petrol_pump": self.petrol_pump, "fuel_type": fuel_type},
				fields=["warehouse"]
			)
			if not tank or not tank[0].warehouse:
				frappe.throw(f"No Fuel Tank with warehouse found for Fuel Type {fuel_type} at {self.petrol_pump}")

			warehouse = tank[0].warehouse
			available_qty = get_stock_balance(
				item_code=fuel_type,
				warehouse=warehouse
			)

			if flt(available_qty) < flt(liters_to_test):
				frappe.throw(f"Insufficient stock for testing Fuel Type {fuel_type} in warehouse {warehouse}. Available: {available_qty}, Required for testing: {liters_to_test}")

	def create_testing_stock_entry(self):
		fuel_consumption = {}
		for detail in self.fuel_testing_details:
			if detail.test_liters > 0:
				fuel_type = detail.fuel_type
				liters = detail.test_liters
				fuel_consumption[fuel_type] = fuel_consumption.get(fuel_type, 0) + liters

		if fuel_consumption:
			stock_entry = frappe.new_doc("Stock Entry")
			stock_entry.stock_entry_type = "Material Issue"
			stock_entry.purpose = "Material Issue"
			stock_entry.company = frappe.db.get_value("Petrol Pump", self.petrol_pump, "company")
			stock_entry.set_posting_time = 1
			stock_entry.posting_date = self.test_date or nowdate()
			stock_entry.add_comment("Comment", f"Fuel Testing - {self.name}")

			for fuel_type, liters in fuel_consumption.items():
				warehouse = frappe.db.get_value("Fuel Tank",
					{"petrol_pump": self.petrol_pump, "fuel_type": fuel_type},
					"warehouse")

				if warehouse:
					# Get actual valuation rate for proper COGS tracking
					valuation_rate = self.get_valuation_rate(fuel_type, warehouse)
					
					stock_entry.append("items", {
						"s_warehouse": warehouse,
						"item_code": fuel_type,
						"qty": liters,
						"basic_rate": valuation_rate,
						"conversion_factor": 1.0
					})

			if stock_entry.items:
				stock_entry.insert()
				stock_entry.submit()
				self.db_set('stock_entry_ref', stock_entry.name)
				frappe.msgprint(f"Stock Entry {stock_entry.name} created for fuel testing")
	
	def get_valuation_rate(self, item_code, warehouse):
		"""Get current valuation rate for accurate COGS tracking"""
		valuation_rate = frappe.db.get_value(
			"Stock Ledger Entry",
			{
				"item_code": item_code,
				"warehouse": warehouse,
				"is_cancelled": 0
			},
			"valuation_rate",
			order_by="posting_date desc, posting_time desc, creation desc"
		)
		return flt(valuation_rate) if valuation_rate else 0
	
	def cancel_stock_entry(self):
		"""Cancel linked Stock Entry"""
		if self.stock_entry_ref:
			try:
				se = frappe.get_doc("Stock Entry", self.stock_entry_ref)
				if se.docstatus == 1:
					se.cancel()
					frappe.msgprint(f"Stock Entry {self.stock_entry_ref} cancelled")
			except Exception as e:
				frappe.throw(f"Error cancelling Stock Entry: {str(e)}")

	@frappe.whitelist()
	def get_available_nozzles(self):
		if not self.petrol_pump:
			return []

		nozzles_data = []
		dispensers = frappe.get_all("Dispenser",
			filters={"petrol_pump": self.petrol_pump, "is_active": 1},
			fields=["name"]
		)

		for dispenser in dispensers:
			dispenser_doc = frappe.get_doc("Dispenser", dispenser.name)
			for nozzle in dispenser_doc.nozzles:
				if nozzle.is_active:
					nozzles_data.append({
						"dispenser": dispenser.name,
						"nozzle_number": nozzle.nozzle_number,
						"fuel_type": nozzle.fuel_type,
						"rate": self.get_current_rate(nozzle.fuel_type)
					})
		return nozzles_data

	def get_current_rate(self, fuel_type):
		rate = frappe.db.sql("""
			SELECT price_per_liter
			FROM `tabFuel Price`
			WHERE fuel_type = %s AND is_active = 1 AND effective_from <= %s
			ORDER BY effective_from DESC LIMIT 1
		""", (fuel_type, get_datetime(self.test_date or nowdate())))
		return rate[0][0] if rate else 0

	@frappe.whitelist()
	def get_nozzle_options(self, dispenser):
		if not dispenser:
			return []

		dispenser_doc = frappe.get_doc("Dispenser", dispenser)
		nozzles = []
		for nozzle in dispenser_doc.nozzles:
			if nozzle.is_active:
				nozzles.append(nozzle.nozzle_number)
		return nozzles
