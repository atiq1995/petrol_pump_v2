import frappe
from frappe.model.document import Document
from frappe.utils import now_datetime

class FuelPrice(Document):
    def before_save(self):
        # If effective_from is not set, use current datetime
        if not self.effective_from:
            self.effective_from = now_datetime()
        
        # Deactivate other active prices for same fuel type
        if self.is_active:
            frappe.db.sql("""
                UPDATE `tabFuel Price` 
                SET is_active = 0 
                WHERE fuel_type = %s AND name != %s AND is_active = 1
            """, (self.fuel_type, self.name))