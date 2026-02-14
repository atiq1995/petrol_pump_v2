import frappe
from frappe.model.document import Document


class FuelPrice(Document):
    def before_save(self):
        """Deactivate other active prices for the same petrol pump + fuel type"""
        if self.is_active:
            frappe.db.sql("""
                UPDATE `tabFuel Price`
                SET is_active = 0
                WHERE fuel_type = %s AND petrol_pump = %s AND name != %s AND is_active = 1
            """, (self.fuel_type, self.petrol_pump, self.name))
