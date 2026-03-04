import frappe
from frappe.model.document import Document
from frappe.utils import flt, getdate, nowdate
from erpnext.stock.utils import get_stock_balance


class TankDipReading(Document):
    def before_save(self):
        self.calculate_totals()

    def calculate_totals(self):
        total_variance = 0.0
        for row in self.tank_readings or []:
            row.difference = flt(row.measured_dip) - flt(row.system_stock)
            total_variance += flt(row.difference)
        self.total_variance = total_variance


@frappe.whitelist()
def get_pump_tank_rows(petrol_pump: str, reading_date: str = None):
    """Return all fuel tanks for a pump with current system stock."""
    if not petrol_pump:
        return []

    posting_date = getdate(reading_date) if reading_date else getdate(nowdate())
    tanks = frappe.get_all(
        "Fuel Tank",
        filters={"petrol_pump": petrol_pump},
        fields=["name", "fuel_type", "warehouse"],
        order_by="name asc",
    )

    rows = []
    for tank in tanks:
        system_stock = 0.0
        if tank.warehouse and tank.fuel_type:
            system_stock = get_stock_balance(
                item_code=tank.fuel_type,
                warehouse=tank.warehouse,
                posting_date=posting_date,
            )

        rows.append(
            {
                "fuel_tank": tank.name,
                "fuel_type": tank.fuel_type,
                "warehouse": tank.warehouse,
                "system_stock": flt(system_stock),
                "measured_dip": 0.0,
                "difference": 0.0,
            }
        )

    return rows
