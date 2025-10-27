from frappe.model.document import Document
import frappe


class FuelType(Document):
    def after_insert(self):
        """Auto-create an Item with the same name as this Fuel Type if it doesn't exist.
        The Item will be a stock item with Stock UOM = Litre so stock can be maintained
        per tank warehouse.
        """
        self._ensure_item_exists()

    def on_update(self):
        # Ensure item always exists even if Fuel Type was imported/renamed
        self._ensure_item_exists()

    def _ensure_item_exists(self):
        item_code = self.name
        if frappe.db.exists("Item", item_code):
            return

        # Pick a safe Item Group
        item_group = (
            frappe.db.exists("Item Group", "All Item Groups")
            or frappe.db.exists("Item Group", "Products")
            or frappe.db.get_single_value("Stock Settings", "default_item_group")
            or "All Item Groups"
        )

        item = frappe.new_doc("Item")
        item.item_code = item_code
        item.item_name = self.fuel_type_name or item_code
        item.item_group = item_group
        item.is_stock_item = 1
        item.stock_uom = "Litre"
        item.insert(ignore_permissions=True)
        frappe.msgprint(f"Item {item.name} auto-created for Fuel Type {self.name}")
