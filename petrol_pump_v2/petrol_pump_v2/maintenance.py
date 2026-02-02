import frappe


@frappe.whitelist()
def purge_old_dispenser_and_day_closing():
    """Delete all Dispenser and Day Closing documents (dangerous)."""
    for doctype in ("Day Closing", "Dispenser"):
        names = frappe.get_all(doctype, pluck="name")
        for name in names:
            try:
                doc = frappe.get_doc(doctype, name)
                # cancel if submittable and submitted
                if getattr(doc, "docstatus", 0) == 1 and hasattr(doc, "cancel"):
                    doc.cancel()
                doc.delete()
            except Exception as e:
                frappe.log_error(f"Failed deleting {doctype} {name}: {e}", "Purge Maintenance")
    frappe.db.commit()
    return "Purged Dispenser and Day Closing documents"


