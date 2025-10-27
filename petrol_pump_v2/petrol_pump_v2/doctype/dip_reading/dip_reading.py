import frappe
from frappe.model.document import Document
from frappe.utils import flt, nowdate
from erpnext.stock.utils import get_stock_balance

class DipReading(Document):
    def before_save(self):
        self.calculate_difference()
    
    def on_submit(self):
        if abs(self.difference) >= 0.1:  # Adjust if difference > 0.1 liters
            self.create_stock_reconciliation()
    
    def on_cancel(self):
        """Cancel linked Stock Reconciliation"""
        self.cancel_stock_reconciliation()
    
    def calculate_difference(self):
        """Calculate difference between physical dip and system stock"""
        if self.fuel_tank:
            # Get system stock from warehouse using ERPNext utility
            tank_doc = frappe.get_doc("Fuel Tank", self.fuel_tank)
            if tank_doc.warehouse and tank_doc.fuel_type:
                self.system_stock = get_stock_balance(
                    item_code=tank_doc.fuel_type,
                    warehouse=tank_doc.warehouse,
                    posting_date=self.reading_date or nowdate()
                )
            else:
                self.system_stock = 0
            self.difference = flt(self.measured_dip) - flt(self.system_stock)
    
    def create_stock_reconciliation(self):
        """Create Stock Reconciliation for variance (proper method as per blueprint)"""
        tank_doc = frappe.get_doc("Fuel Tank", self.fuel_tank)
        
        if not tank_doc.warehouse or not tank_doc.fuel_type:
            frappe.throw("Fuel Tank must have a valid Warehouse and Fuel Type")
        
        # Get current valuation rate
        valuation_rate = frappe.db.get_value(
            "Stock Ledger Entry",
            {
                "item_code": tank_doc.fuel_type,
                "warehouse": tank_doc.warehouse,
                "is_cancelled": 0
            },
            "valuation_rate",
            order_by="posting_date desc, posting_time desc"
        ) or 0
        
        # Create Stock Reconciliation
        stock_recon = frappe.new_doc("Stock Reconciliation")
        stock_recon.purpose = "Stock Reconciliation"
        stock_recon.company = frappe.db.get_value("Petrol Pump", self.petrol_pump, "company")
        stock_recon.posting_date = self.reading_date or nowdate()
        stock_recon.set_posting_time = 1
        
        stock_recon.append("items", {
            "item_code": tank_doc.fuel_type,
            "warehouse": tank_doc.warehouse,
            "qty": flt(self.measured_dip),  # Set to actual measured quantity
            "valuation_rate": valuation_rate,
            "current_qty": flt(self.system_stock),
            "current_valuation_rate": valuation_rate
        })
        
        stock_recon.insert()
        stock_recon.submit()
        self.db_set('stock_reconciliation_ref', stock_recon.name)
        
        frappe.msgprint(f"Stock Reconciliation {stock_recon.name} created for variance of {self.difference} liters")
    
    def cancel_stock_reconciliation(self):
        """Cancel linked Stock Reconciliation"""
        if self.stock_reconciliation_ref:
            try:
                sr = frappe.get_doc("Stock Reconciliation", self.stock_reconciliation_ref)
                if sr.docstatus == 1:
                    sr.cancel()
                    frappe.msgprint(f"Stock Reconciliation {self.stock_reconciliation_ref} cancelled")
            except Exception as e:
                frappe.throw(f"Error cancelling Stock Reconciliation: {str(e)}")