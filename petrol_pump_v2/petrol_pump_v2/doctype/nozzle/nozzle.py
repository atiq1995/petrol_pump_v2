import frappe
from frappe.model.document import Document


class Nozzle(Document):
    def validate(self):
        self._set_fuel_type_from_tank()
        self._validate_links()
        self._initialize_last_reading()
    
    def _initialize_last_reading(self):
        """Initialize last_reading from opening_reading if last_reading is 0 and opening_reading exists"""
        if not self.last_reading or self.last_reading == 0:
            if self.opening_reading and self.opening_reading > 0:
                self.last_reading = self.opening_reading

    def _set_fuel_type_from_tank(self):
        if self.fuel_tank:
            tank_fuel = frappe.db.get_value("Fuel Tank", self.fuel_tank, "fuel_type")
            if tank_fuel and self.fuel_type != tank_fuel:
                self.fuel_type = tank_fuel

    def _validate_links(self):
        if self.petrol_pump and self.fuel_tank:
            tank_pump = frappe.db.get_value("Fuel Tank", self.fuel_tank, "petrol_pump")
            if tank_pump and tank_pump != self.petrol_pump:
                frappe.throw(
                    f"Fuel Tank '{self.fuel_tank}' belongs to petrol pump '{tank_pump}', "
                    f"but Nozzle is linked to '{self.petrol_pump}'. They must match."
                )

