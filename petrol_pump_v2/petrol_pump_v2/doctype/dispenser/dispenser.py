import frappe
from frappe.model.document import Document

class Dispenser(Document):
    def validate(self):
        # Auto-set fuel_type for each nozzle from fuel_tank
        for nozzle in self.nozzles:
            if nozzle.fuel_tank and not nozzle.fuel_type:
                tank = frappe.get_doc("Fuel Tank", nozzle.fuel_tank)
                nozzle.fuel_type = tank.fuel_type