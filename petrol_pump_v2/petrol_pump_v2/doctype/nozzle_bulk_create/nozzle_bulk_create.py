import frappe
from frappe.model.document import Document


class NozzleBulkCreate(Document):
    def validate(self):
        self._validate_rows()

    def on_submit(self):
        # Ensure naming series exists in Series table (key is "NOZ" without dash)
        if not frappe.db.exists("Series", "NOZ"):
            frappe.db.sql("INSERT INTO `tabSeries` (name, current) VALUES ('NOZ', 0)")
            frappe.db.commit()
        
        # Clear cache and reload Nozzle DocType to ensure correct module path
        frappe.clear_cache(doctype="Nozzle")
        try:
            frappe.reload_doc("petrol_pump_v2", "doctype", "nozzle", force=True)
        except Exception:
            # If reload fails, continue anyway - might work with cached version
            pass
        
        created = []
        skipped = []
        for idx, row in enumerate(self.nozzles_to_create, 1):
            if not row.nozzle_name or not row.fuel_tank:
                skipped.append((row.nozzle_name or "(blank)", "Missing required fields"))
                continue

            # Ensure tank belongs to selected petrol pump
            tank_pump = frappe.db.get_value("Fuel Tank", row.fuel_tank, "petrol_pump")
            if tank_pump and tank_pump != self.petrol_pump:
                skipped.append((row.nozzle_name, f"Fuel Tank belongs to {tank_pump}"))
                continue

            # Check duplicate within same pump
            if frappe.db.exists("Nozzle", {"petrol_pump": self.petrol_pump, "nozzle_name": row.nozzle_name}):
                skipped.append((row.nozzle_name, "Already exists"))
                continue

            try:
                doc = frappe.new_doc("Nozzle")
                # Set naming series first (required for autoname)
                doc.naming_series = "NOZ-"
                doc.nozzle_name = row.nozzle_name
                doc.petrol_pump = self.petrol_pump
                doc.fuel_tank = row.fuel_tank
                doc.fuel_type = frappe.db.get_value("Fuel Tank", row.fuel_tank, "fuel_type")
                doc.opening_reading = row.opening_reading or 0
                doc.is_active = 1 if (row.is_active is None or row.is_active == 1) else 0
                
                # Insert with proper error handling
                doc.insert(ignore_permissions=True)
                frappe.db.commit()
                
                if doc.name:
                    created.append(doc.name)
                else:
                    skipped.append((row.nozzle_name, "No ID generated"))
            except Exception as e:
                error_msg = str(e)
                skipped.append((row.nozzle_name, f"Error: {error_msg}"))
                frappe.log_error(f"Error creating nozzle {row.nozzle_name} in row {idx}: {error_msg}")

        # Save a summary
        summary_lines = []
        if created:
            summary_lines.append("Created: " + ", ".join(created))
        if skipped:
            parts = [f"{name} ({reason})" for name, reason in skipped]
            summary_lines.append("Skipped: " + ", ".join(parts))
        self.created_summary = "\n".join(summary_lines)

    def on_cancel(self):
        """Handle cancellation - note that created nozzles are not auto-deleted
        as they may be in use. User must manually delete them if needed.
        """
        frappe.msgprint(
            "Note: The Nozzle records created by this bulk operation were not deleted. "
            "You may need to manually delete them if they are no longer needed.",
            indicator="orange",
            alert=True
        )

    def _validate_rows(self):
        names = set()
        for row in self.nozzles_to_create:
            if not row.nozzle_name:
                frappe.throw("Nozzle Name is required in all rows")
            if row.nozzle_name in names:
                frappe.throw(f"Duplicate Nozzle Name in rows: {row.nozzle_name}")
            names.add(row.nozzle_name)

