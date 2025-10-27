import frappe
from frappe.model.document import Document
from frappe.utils import flt
from erpnext.stock.utils import get_stock_balance

class FuelTransfer(Document):
    def validate(self):
        """Validate stock availability and fuel type consistency"""
        self.validate_fuel_type_consistency()
        self.validate_stock_availability()
    
    def before_save(self):
        # Auto-set fuel_type from source tank
        if self.from_fuel_tank and not self.fuel_type:
            from_tank = frappe.get_doc("Fuel Tank", self.from_fuel_tank)
            self.fuel_type = from_tank.fuel_type
    
    def validate_fuel_type_consistency(self):
        """Ensure source and destination tanks have same fuel type"""
        from_tank = frappe.get_doc("Fuel Tank", self.from_fuel_tank)
        to_tank = frappe.get_doc("Fuel Tank", self.to_fuel_tank)
        
        if from_tank.fuel_type != to_tank.fuel_type:
            frappe.throw(
                f"Cannot transfer fuel between different fuel types. "
                f"Source tank ({from_tank.tank_name}) has {from_tank.fuel_type}, "
                f"but destination tank ({to_tank.tank_name}) has {to_tank.fuel_type}."
            )
    
    def validate_stock_availability(self):
        """Validate sufficient stock in source tank before transfer"""
        if not self.from_fuel_tank or not self.quantity:
            return
        
        from_tank = frappe.get_doc("Fuel Tank", self.from_fuel_tank)
        
        if not from_tank.warehouse:
            frappe.throw(f"Source tank {from_tank.tank_name} does not have a warehouse configured")
        
        # Get available stock in source warehouse
        available_qty = get_stock_balance(
            item_code=self.fuel_type,
            warehouse=from_tank.warehouse
        )
        
        if flt(available_qty) < flt(self.quantity):
            frappe.throw(
                f"Insufficient stock in source tank {from_tank.tank_name}. "
                f"Available: {available_qty} liters, Requested: {self.quantity} liters. "
                f"Short by: {flt(self.quantity) - flt(available_qty)} liters."
            )
    
    def on_submit(self):
        self.create_stock_entry()
    
    def on_cancel(self):
        """Cancel linked Stock Entry"""
        self.cancel_stock_entry()
    
    def create_stock_entry(self):
        """Create stock entry for fuel transfer with proper valuation"""
        stock_entry = frappe.new_doc("Stock Entry")
        stock_entry.stock_entry_type = "Material Transfer"
        stock_entry.purpose = "Material Transfer"
        
        from_tank = frappe.get_doc("Fuel Tank", self.from_fuel_tank)
        to_tank = frappe.get_doc("Fuel Tank", self.to_fuel_tank)
        
        stock_entry.company = frappe.db.get_value("Petrol Pump", self.from_petrol_pump, "company")
        stock_entry.set_posting_time = 1
        stock_entry.posting_date = self.transfer_date
        
        # Get actual valuation rate for proper cost tracking
        valuation_rate = self.get_valuation_rate(self.fuel_type, from_tank.warehouse)
        
        # Add transfer item
        stock_entry.append("items", {
            "s_warehouse": from_tank.warehouse,
            "t_warehouse": to_tank.warehouse,
            "item_code": self.fuel_type,
            "qty": self.quantity,
            "basic_rate": valuation_rate,
            "conversion_factor": 1.0
        })
        
        stock_entry.insert()
        stock_entry.submit()
        self.db_set('stock_entry_ref', stock_entry.name)
        
        frappe.msgprint(f"Stock Entry {stock_entry.name} created for fuel transfer of {self.quantity} liters")
    
    def get_valuation_rate(self, item_code, warehouse):
        """Get current valuation rate for accurate cost tracking"""
        valuation_rate = frappe.db.get_value(
            "Stock Ledger Entry",
            {
                "item_code": item_code,
                "warehouse": warehouse,
                "is_cancelled": 0
            },
            "valuation_rate",
            order_by="posting_date desc, posting_time desc, creation desc"
        )
        return flt(valuation_rate) if valuation_rate else 0
    
    def cancel_stock_entry(self):
        """Cancel linked Stock Entry"""
        if self.stock_entry_ref:
            try:
                se = frappe.get_doc("Stock Entry", self.stock_entry_ref)
                if se.docstatus == 1:
                    se.cancel()
                    frappe.msgprint(f"Stock Entry {self.stock_entry_ref} cancelled")
            except Exception as e:
                frappe.throw(f"Error cancelling Stock Entry: {str(e)}")
        
