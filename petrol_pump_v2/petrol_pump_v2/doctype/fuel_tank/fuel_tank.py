import frappe
from frappe.model.document import Document
from frappe.utils import flt
from erpnext.stock.utils import get_stock_balance

class FuelTank(Document):
    def validate(self):
        self.ensure_warehouse_exists()
        self.validate_warehouse_and_fuel_type()
        self.update_current_stock()
    
    def ensure_warehouse_exists(self):
        """Auto-create warehouse if it doesn't exist, using tank_name as the base name"""
        if not self.tank_name or not self.petrol_pump:
            return
        
        # If warehouse is already set and exists, don't auto-create
        if self.warehouse and frappe.db.exists("Warehouse", self.warehouse):
            return
        
        # Get company from Petrol Pump
        company = frappe.db.get_value("Petrol Pump", self.petrol_pump, "company")
        if not company:
            frappe.throw(f"Company not found for Petrol Pump {self.petrol_pump}")
        
        # Get company abbreviation
        company_abbr = frappe.get_cached_value("Company", company, "abbr")
        
        # Build warehouse name: tank_name (ERPNext will automatically append company abbreviation)
        warehouse_name = self.tank_name
        
        # Check if warehouse already exists (with company suffix)
        warehouse_with_suffix = f"{warehouse_name} - {company_abbr}"
        
        if frappe.db.exists("Warehouse", warehouse_with_suffix):
            # Warehouse already exists, use it
            self.warehouse = warehouse_with_suffix
            return
        
        # Create new warehouse
        try:
            warehouse = frappe.new_doc("Warehouse")
            warehouse.warehouse_name = warehouse_name
            warehouse.company = company
            warehouse.is_group = 0  # Storage warehouse, not a group
            warehouse.insert(ignore_permissions=True)
            
            # Set the warehouse field (ERPNext autoname will have added the company suffix)
            self.warehouse = warehouse.name
            
            frappe.msgprint(
                f"Warehouse '{warehouse.name}' auto-created for Fuel Tank '{self.tank_name}'",
                indicator="green",
                alert=True
            )
        except Exception as e:
            error_msg = f"Error auto-creating warehouse for Fuel Tank {self.tank_name}: {str(e)}"
            frappe.log_error(error_msg, "Fuel Tank Warehouse Auto-Creation Error")
            frappe.throw(f"Failed to auto-create warehouse. {str(e)}")
    
    def validate_warehouse_and_fuel_type(self):
        """Validate that warehouse and fuel type are properly configured"""
        if self.warehouse:
            # Check if warehouse exists
            if not frappe.db.exists("Warehouse", self.warehouse):
                frappe.throw(f"Warehouse {self.warehouse} does not exist")
            
            # Validate warehouse belongs to same company as Petrol Pump
            if self.petrol_pump:
                company = frappe.db.get_value("Petrol Pump", self.petrol_pump, "company")
                warehouse_company = frappe.db.get_value("Warehouse", self.warehouse, "company")
                if company and warehouse_company and company != warehouse_company:
                    frappe.throw(
                        f"Warehouse '{self.warehouse}' belongs to company '{warehouse_company}', "
                        f"but Petrol Pump '{self.petrol_pump}' belongs to company '{company}'. "
                        f"They must match."
                    )
        
        if self.fuel_type:
            # Check if fuel type (item) exists
            if not frappe.db.exists("Item", self.fuel_type):
                frappe.msgprint(
                    f"Item {self.fuel_type} does not exist. Please create it or ensure Fuel Type is properly configured.",
                    indicator="orange",
                    alert=True
                )
    
    def update_current_stock(self):
        """Update current stock from warehouse bin with proper error handling"""
        if not self.warehouse or not self.fuel_type:
            self.current_stock = 0
            return
        
        try:
            # Use ERPNext utility function for accurate stock balance
            stock_qty = get_stock_balance(
                item_code=self.fuel_type,
                warehouse=self.warehouse
            )
            self.current_stock = flt(stock_qty)
            
        except Exception as e:
            error_msg = f"Error updating fuel tank stock for {self.name}: {str(e)}"
            frappe.log_error(error_msg, "Fuel Tank Stock Update Error")
            
            # Show user-friendly message
            frappe.msgprint(
                f"Could not fetch current stock. Please ensure Warehouse '{self.warehouse}' and Item '{self.fuel_type}' are properly configured. "
                f"Error: {str(e)}",
                indicator="red",
                alert=True
            )
            
            # Set to 0 but don't silently fail
            self.current_stock = 0