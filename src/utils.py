def calculate_booking_cost(hours):
    base_cost = 45000
    additional_hour_cost = 9000
    total_cost = base_cost

    if hours > 6:
        additional_hours = hours - 6
        total_cost += additional_hours * additional_hour_cost

    return total_cost

def calculate_end_time(start_time, hours):
    from datetime import timedelta

    end_time = start_time + timedelta(hours=hours)
    return end_time

def is_room_available(room_status, room_number):
    return room_status.get(room_number, False) == False

def book_room(room_status, room_number):
    if is_room_available(room_status, room_number):
        room_status[room_number] = True
        return True
    return False

def release_room(room_status, room_number):
    if room_status.get(room_number, False):
        room_status[room_number] = False
        return True
    return False

# Módulo de utilidades para inventario de productos

class Product:
    _code_counter = 1

    def __init__(self, name, quantity, price):
        self.name = name
        self.code = Product._code_counter
        Product._code_counter += 1
        self.quantity = quantity
        self.price = price

    def to_dict(self):
        return {
            "name": self.name,
            "code": self.code,
            "quantity": self.quantity,
            "price": self.price
        }

class Inventory:
    def __init__(self):
        self.products = []

    def add_product(self, name, quantity, price):
        product = Product(name, quantity, price)
        self.products.append(product)
        return product.code

    def get_products(self):
        return [p.to_dict() for p in self.products]

    def update_quantity(self, code, amount):
        for p in self.products:
            if p.code == code:
                p.quantity += amount
                return True
        return False

    def remove_product(self, code):
        for i, p in enumerate(self.products):
            if p.code == code:
                del self.products[i]
                return True
        return False

import csv
from datetime import datetime

class CashRegister:
    def __init__(self):
        self.opening_amount = 0
        self.sales = []  # dict: {"amount": x, "method": "efectivo"/"datáfono"/"nequi"/...}
        self.movements = []  # dict: {"amount": x, "type": "ingreso"/"egreso", "desc": str}
        self.denominations = {}  # opcional: {denom: cantidad}
        self.closed = False

    def open_cash(self, amount):
        self.opening_amount = amount

    def add_sale(self, amount, method):
        self.sales.append({"amount": amount, "method": method})

    def add_movement(self, amount, mov_type, desc):
        self.movements.append({"amount": amount, "type": mov_type, "desc": desc})

    def set_denominations(self, denominations_dict):
        self.denominations = denominations_dict

    def get_totals_by_method(self):
        totals = {}
        for sale in self.sales:
            method = sale["method"]
            totals[method] = totals.get(method, 0) + sale["amount"]
        return totals

    def get_total_sales(self):
        return sum(s["amount"] for s in self.sales)

    def get_total_ingresos(self):
        return sum(m["amount"] for m in self.movements if m["type"] == "ingreso")

    def get_total_egresos(self):
        return sum(m["amount"] for m in self.movements if m["type"] == "egreso")

    def get_expected_total(self):
        return self.opening_amount + self.get_total_sales() + self.get_total_ingresos() - self.get_total_egresos()

    def get_counted_total(self):
        # Suma de denominaciones (opcional)
        return sum(int(denom) * int(qty) for denom, qty in self.denominations.items())

    def get_summary(self):
        return {
            "apertura": self.opening_amount,
            "ventas": self.get_total_sales(),
            "ingresos": self.get_total_ingresos(),
            "egresos": self.get_total_egresos(),
            "esperado": self.get_expected_total(),
            "contado": self.get_counted_total(),
            "diferencia": self.get_counted_total() - self.get_expected_total(),
            "por_metodo": self.get_totals_by_method()
        }

    def close_cash(self, filename):
        self.closed = True
        with open(filename, "w", newline='', encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(["Reporte de Caja", datetime.now().strftime("%Y-%m-%d %H:%M:%S")])
            writer.writerow([])
            writer.writerow(["Apertura", self.opening_amount])
            writer.writerow(["Total Ventas", self.get_total_sales()])
            writer.writerow(["Total Ingresos", self.get_total_ingresos()])
            writer.writerow(["Total Egresos", self.get_total_egresos()])
            writer.writerow(["Total Esperado", self.get_expected_total()])
            writer.writerow(["Total Contado", self.get_counted_total()])
            writer.writerow(["Diferencia", self.get_counted_total() - self.get_expected_total()])
            writer.writerow([])
            writer.writerow(["Ventas por método"])
            for method, total in self.get_totals_by_method().items():
                writer.writerow([method, total])
            writer.writerow([])
            writer.writerow(["Movimientos"])
            writer.writerow(["Tipo", "Monto", "Descripción"])
            for m in self.movements:
                writer.writerow([m["type"], m["amount"], m["desc"]])
            if self.denominations:
                writer.writerow([])
                writer.writerow(["Denominaciones"])
                for denom, qty in self.denominations.items():
                    writer.writerow([denom, qty, int(denom)*int(qty)])