import frappe
from frappe.model.document import Document


class FuelPrice(Document):
    def before_save(self):
        """Deactivate other active Fuel Price records for the same petrol pump"""
        if self.is_active:
            frappe.db.sql("""
                UPDATE `tabFuel Price`
                SET is_active = 0
                WHERE petrol_pump = %s AND name != %s AND is_active = 1
            """, (self.petrol_pump, self.name))
