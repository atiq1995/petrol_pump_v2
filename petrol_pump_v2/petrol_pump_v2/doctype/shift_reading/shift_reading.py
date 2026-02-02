import frappe
from frappe.model.document import Document
from frappe.utils import flt, nowdate, now_datetime
from erpnext.stock.utils import get_stock_balance

class ShiftReading(Document):
    def validate(self):
        """Validate prices for all nozzle readings"""
        self.validate_prices()
    
    def validate_prices(self):
        """Ensure all nozzle readings have valid prices"""
        for d in self.nozzle_readings or []:
            if d.dispensed_liters and d.dispensed_liters > 0:
                if not d.rate or flt(d.rate) <= 0:
                    frappe.throw(
                        f"Price is missing or zero for {d.fuel_type} on Dispenser {d.dispenser}, Nozzle {d.nozzle_number}. "
                        "Please ensure active Fuel Price exists for the reading date."
                    )
    
    def before_save(self):
        self.populate_nozzle_readings()
        self.calculate_readings()
    
    def on_submit(self):
        self.create_stock_entry()
        self.update_nozzle_last_readings()
        self.close_shift()
    
    def on_cancel(self):
        """Cancel linked Stock Entry and revert nozzle readings"""
        self.cancel_stock_entry()
        self.revert_nozzle_readings()
        self.reopen_shift()
    
    def populate_nozzle_readings(self):
        """Auto-populate nozzle readings table from standalone Nozzles"""
        if not self.nozzle_readings and self.petrol_pump:
            # Clear existing rows if any
            self.set('nozzle_readings', [])

            nozzles = frappe.get_all(
                "Nozzle",
                filters={"petrol_pump": self.petrol_pump, "is_active": 1},
                fields=["name", "nozzle_name", "fuel_type", "last_reading"],
            )

            for n in nozzles:
                self.append("nozzle_readings", {
                    # keep columns compatible with existing child schema
                    "dispenser": None,
                    "nozzle_number": n.nozzle_name,
                    "fuel_type": n.fuel_type,
                    "previous_reading": n.last_reading or 0,
                    "current_reading": 0,
                    "rate": self.get_current_rate(n.fuel_type),
                })
    
    def calculate_readings(self):
        """Calculate dispensed liters and amounts"""
        total_sales = 0
        total_liters = 0
        
        for nozzle_reading in self.nozzle_readings:
            # Calculate dispensed liters
            nozzle_reading.dispensed_liters = flt(nozzle_reading.current_reading) - flt(nozzle_reading.previous_reading)
            
            # Calculate amount
            if not nozzle_reading.rate:
                nozzle_reading.rate = self.get_current_rate(nozzle_reading.fuel_type)
            
            nozzle_reading.amount = flt(nozzle_reading.dispensed_liters) * flt(nozzle_reading.rate)
            
            total_sales += flt(nozzle_reading.amount)
            total_liters += flt(nozzle_reading.dispensed_liters)
        
        self.total_sales = total_sales
        self.total_liters = total_liters
    
    def get_current_rate(self, fuel_type):
        """Get current active fuel price (effective now or earlier)"""
        if not fuel_type:
            return 0
        rate = frappe.db.sql(
            """
            SELECT price_per_liter 
            FROM `tabFuel Price` 
            WHERE fuel_type = %s AND is_active = 1 AND effective_from <= %s
            ORDER BY effective_from DESC LIMIT 1
            """,
            (fuel_type, now_datetime()),
        )
        return rate[0][0] if rate else 0
    
    def create_stock_entry(self):
        """Create stock entry for fuel consumption"""
        # Group consumption by fuel type
        fuel_consumption = {}
        
        for nozzle_reading in self.nozzle_readings:
            if nozzle_reading.dispensed_liters > 0:
                fuel_type = nozzle_reading.fuel_type
                liters = nozzle_reading.dispensed_liters
                
                if fuel_type in fuel_consumption:
                    fuel_consumption[fuel_type] += liters
                else:
                    fuel_consumption[fuel_type] = liters
        
        # Create stock entry
        if fuel_consumption:
            stock_entry = frappe.new_doc("Stock Entry")
            stock_entry.stock_entry_type = "Material Issue"
            stock_entry.purpose = "Material Issue"
            stock_entry.company = frappe.db.get_value("Petrol Pump", self.petrol_pump, "company")
            stock_entry.set_posting_time = 1
            stock_entry.posting_date = self.reading_date or nowdate()
            
            for fuel_type, liters in fuel_consumption.items():
                # Find warehouse for this fuel type
                warehouse = frappe.db.get_value("Fuel Tank", 
                    {"petrol_pump": self.petrol_pump, "fuel_type": fuel_type}, 
                    "warehouse")
                
                if warehouse:
                    # Get actual valuation rate for proper COGS tracking
                    valuation_rate = self.get_valuation_rate(fuel_type, warehouse)
                    
                    stock_entry.append("items", {
                        "s_warehouse": warehouse,
                        "item_code": fuel_type,
                        "qty": liters,
                        "basic_rate": valuation_rate,
                        "conversion_factor": 1.0
                    })
            
            if stock_entry.items:
                stock_entry.insert()
                stock_entry.submit()
                self.db_set('stock_entry_ref', stock_entry.name)
                frappe.msgprint(f"Stock Entry {stock_entry.name} created for fuel consumption")
    
    def get_valuation_rate(self, item_code, warehouse):
        """Get current valuation rate for accurate COGS tracking"""
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
    
    def update_nozzle_last_readings(self):
        """Update last_reading in Nozzle master"""
        for nozzle_reading in self.nozzle_readings or []:
            # Match by petrol_pump + nozzle_name
            nozzle_name = nozzle_reading.nozzle_number
            if nozzle_name:
                nn = frappe.db.get_value(
                    "Nozzle",
                    {"petrol_pump": self.petrol_pump, "nozzle_name": nozzle_name},
                    "name",
                )
                if nn:
                    frappe.db.set_value("Nozzle", nn, "last_reading", flt(nozzle_reading.current_reading))
    
    def close_shift(self):
        """Mark shift as closed"""
        if self.shift:
            frappe.db.set_value("Shift", self.shift, "status", "Closed")
    
    def reopen_shift(self):
        """Reopen shift when reading is cancelled"""
        if self.shift:
            frappe.db.set_value("Shift", self.shift, "status", "Open")
            frappe.msgprint(f"Shift {self.shift} reopened")
    
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
    
    def revert_nozzle_readings(self):
        """Revert nozzle last readings on Nozzle master"""
        for nozzle_reading in self.nozzle_readings or []:
            nozzle_name = nozzle_reading.nozzle_number
            if nozzle_name:
                nn = frappe.db.get_value(
                    "Nozzle",
                    {"petrol_pump": self.petrol_pump, "nozzle_name": nozzle_name},
                    "name",
                )
                if nn:
                    frappe.db.set_value("Nozzle", nn, "last_reading", flt(nozzle_reading.previous_reading))
        frappe.msgprint("Nozzle readings reverted")

@frappe.whitelist()
def get_active_nozzles(petrol_pump: str):
    """Return active nozzles for a petrol pump with defaults for child rows (standalone Nozzle)."""
    rows = []
    if not petrol_pump:
        return rows
    nozzles = frappe.get_all(
        "Nozzle",
        filters={"petrol_pump": petrol_pump, "is_active": 1},
        fields=["nozzle_name", "fuel_type", "last_reading"],
    )
    for n in nozzles:
        rows.append({
            "dispenser": None,
            "nozzle_number": n.nozzle_name,
            "fuel_type": n.fuel_type,
            "previous_reading": n.last_reading or 0,
            "current_reading": 0,
            "rate": ShiftReading.get_current_rate(ShiftReading, n.fuel_type),
        })
    return rows