import frappe
from frappe.model.document import Document
from frappe.utils import now_datetime

class Shift(Document):
    def before_save(self):
        # Auto-set start_time if not set
        if not self.start_time:
            self.start_time = now_datetime()
    
    def on_update(self):
        # If status changed to Closed, set end_time
        if self.status == "Closed" and not self.db_get("end_time"):
            self.db_set("end_time", now_datetime())