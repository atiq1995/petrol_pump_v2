import frappe
from frappe.model.document import Document
from frappe.utils import flt, nowdate, get_datetime
from erpnext.stock.utils import get_stock_balance


class FuelTesting(Document):
	def before_save(self):
		self.populate_nozzle_details()
		self.calculate_totals()
		self.validate_stock_availability()

	def on_submit(self):
		self.create_testing_stock_entry()
		self.update_nozzle_readings()

	def on_cancel(self):
		"""Cancel linked Stock Entry and revert nozzle readings"""
		self.cancel_stock_entry()
		self.revert_nozzle_readings()

	def populate_nozzle_details(self):
		"""Auto-fill fuel_type, rate, amount from selected nozzle"""
		for row in self.fuel_testing_details:
			if row.nozzle:
				nozzle_doc = frappe.get_cached_doc("Nozzle", row.nozzle)
				row.fuel_type = nozzle_doc.fuel_type

				if row.fuel_type:
					row.rate = self.get_current_rate(row.fuel_type)
				row.amount = flt(row.test_liters) * flt(row.rate)

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
			if flt(detail.test_liters) > 0 and detail.fuel_type:
				fuel_type = detail.fuel_type
				liters = flt(detail.test_liters)
				fuel_consumption[fuel_type] = fuel_consumption.get(fuel_type, 0) + liters

		for fuel_type, liters_to_test in fuel_consumption.items():
			tank = frappe.get_all("Fuel Tank",
				filters={"petrol_pump": self.petrol_pump, "fuel_type": fuel_type},
				fields=["name", "warehouse", "tank_name"]
			)
			if not tank or not tank[0].warehouse:
				fuel_name = frappe.db.get_value("Fuel Type", fuel_type, "fuel_type_name") or fuel_type
				frappe.throw(f"No Fuel Tank with warehouse found for {fuel_name} at {self.petrol_pump}")

			warehouse = tank[0].warehouse
			available_qty = get_stock_balance(
				item_code=fuel_type,
				warehouse=warehouse
			)

			if flt(available_qty) < flt(liters_to_test):
				fuel_name = frappe.db.get_value("Fuel Type", fuel_type, "fuel_type_name") or fuel_type
				tank_name = tank[0].tank_name or tank[0].name
				frappe.throw(
					f"Insufficient stock for testing {fuel_name} in {tank_name} ({warehouse}). "
					f"Available: {available_qty:.2f} L, Required: {liters_to_test:.2f} L"
				)

	def update_nozzle_readings(self):
		"""Increase nozzle last_reading by test_liters on submit"""
		for row in self.fuel_testing_details:
			if row.nozzle and flt(row.test_liters) > 0:
				current_reading = flt(frappe.db.get_value("Nozzle", row.nozzle, "last_reading"))
				new_reading = current_reading + flt(row.test_liters)
				frappe.db.set_value("Nozzle", row.nozzle, "last_reading", new_reading)
				nozzle_name = frappe.db.get_value("Nozzle", row.nozzle, "nozzle_name") or row.nozzle
				frappe.msgprint(
					f"Nozzle {nozzle_name}: Reading updated from {current_reading:.2f} to {new_reading:.2f}",
					indicator="green"
				)

	def revert_nozzle_readings(self):
		"""Decrease nozzle last_reading by test_liters on cancel"""
		for row in self.fuel_testing_details:
			if row.nozzle and flt(row.test_liters) > 0:
				current_reading = flt(frappe.db.get_value("Nozzle", row.nozzle, "last_reading"))
				reverted_reading = current_reading - flt(row.test_liters)
				# Ensure reading doesn't go below zero
				reverted_reading = max(reverted_reading, 0)
				frappe.db.set_value("Nozzle", row.nozzle, "last_reading", reverted_reading)
				nozzle_name = frappe.db.get_value("Nozzle", row.nozzle, "nozzle_name") or row.nozzle
				frappe.msgprint(
					f"Nozzle {nozzle_name}: Reading reverted from {current_reading:.2f} to {reverted_reading:.2f}",
					indicator="orange"
				)

	def create_testing_stock_entry(self):
		fuel_consumption = {}
		for detail in self.fuel_testing_details:
			if flt(detail.test_liters) > 0 and detail.fuel_type:
				fuel_type = detail.fuel_type
				liters = flt(detail.test_liters)
				fuel_consumption[fuel_type] = fuel_consumption.get(fuel_type, 0) + liters

		if not fuel_consumption:
			return

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

	def get_current_rate(self, fuel_type):
		if not self.petrol_pump:
			return 0
		rate = frappe.db.sql("""
			SELECT fpd.price_per_liter
			FROM `tabFuel Price Detail` fpd
			JOIN `tabFuel Price` fp ON fpd.parent = fp.name
			WHERE fpd.fuel_type = %s AND fp.petrol_pump = %s AND fp.effective_from <= %s
			ORDER BY fp.effective_from DESC LIMIT 1
		""", (fuel_type, self.petrol_pump, get_datetime(self.test_date or nowdate())))
		return rate[0][0] if rate else 0
