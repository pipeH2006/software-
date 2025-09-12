import tkinter as tk
from tkinter import messagebox, simpledialog
from rooms import RoomManager
import tkinter.ttk as ttk
from datetime import datetime
from rooms import calculate_room_price
from utils import Inventory

class MainWindow(tk.Frame):
    def __init__(self, master, is_admin=False, room_manager=None, timers=None, on_logout=None, conn=None):
        super().__init__(master)
        self.room_manager = room_manager
        self.is_admin = is_admin
        self.on_logout = on_logout
        self.timers = timers if timers is not None else {}
        self.conn = conn  # <-- almacena la conexión MySQL
        self.status_labels = []
        self.timer_labels = {}
        # Asegura que caja_efectivo siempre exista
        self.caja_efectivo = getattr(self, "caja_efectivo", 0)
        self.room_accounts = {}  # {room_number: {"charges": [], "payments": []}}
        self.inventory = Inventory()
        self.create_widgets()
        self.update_room_status()
        # Reiniciar los timers visuales para habitaciones ocupadas
        for room in self.room_manager.rooms:
            if room.status == "ocupada" and room.room_number in self.timers:
                self.start_timer(room.room_number)

    def create_widgets(self):
        tk.Label(self, text="Gestión de Habitaciones", font=("Arial", 16)).pack(pady=10)
        self.rooms_frame = tk.Frame(self)
        self.rooms_frame.pack(pady=10)

        for i in range(22):
            row = i // 2
            col = (i % 2) * 2
            btn = tk.Button(
                self.rooms_frame,
                text="",
                width=25,
                relief="ridge",
                command=lambda n=i+1: self.handle_room_click(n)
            )
            btn.grid(row=row, column=col, padx=5, pady=2)
            self.status_labels.append(btn)
            timer_label = tk.Label(self.rooms_frame, text="", width=10)
            timer_label.grid(row=row, column=col+1)
            self.timer_labels[i+1] = timer_label

        if self.is_admin:
            tk.Button(self, text="Inventario", command=self.open_inventory).pack(pady=5)
            tk.Button(self, text="esinventario", command=self.esinventario).pack(pady=5)
            tk.Button(self, text="esdinero", command=self.esdinero).pack(pady=5)
            tk.Button(self, text="basecaja", command=self.basecaja).pack(pady=5)
            tk.Button(self, text="Añadir trabajador", command=self.add_worker).pack(pady=5)
            tk.Button(self, text="Movimientos de caja", command=self.ver_movimientos_caja).pack(pady=5)

        logout_btn = tk.Button(self, text="Cerrar sesión", command=self.logout)
        logout_btn.pack(pady=5)

    def update_room_status(self):
        status = self.room_manager.get_room_status()
        for i, (num, state) in enumerate(status):
            if state == "disponible":
                text = f"Habitación {num}: Disponible"
                color = "green"
                self.timer_labels[num].config(text="")
            elif state == "ocupada":
                if num in self.timers:
                    mins, secs = divmod(self.timers[num], 60)
                    tiempo = f" | Tiempo: {mins}:{secs:02d}"
                    self.timer_labels[num].config(text=f"{mins}:{secs:02d}")
                else:
                    tiempo = ""
                    self.timer_labels[num].config(text="")
                text = f"Habitación {num}: Ocupada{tiempo}"
                color = "red"
            else:
                text = f"Habitación {num}: Limpieza"
                color = "orange"
                self.timer_labels[num].config(text="")
            self.status_labels[i].config(text=text, bg=color)

    def handle_room_click(self, room_number):
        room = next((r for r in self.room_manager.rooms if r.room_number == room_number), None)
        if not room:
            tk.messagebox.showerror("Error", "Habitación no encontrada.")
            return

        if room.status == "disponible":
            confirm = tk.messagebox.askyesno("Iniciar tiempo", "¿Desea iniciar el tiempo de la habitación?")
            if confirm:
                room.status = "ocupada"
                self.timers[room_number] = 60  # 1 minuto
                self.update_room_status()
                self.start_timer(room_number)
        elif room.status == "ocupada":
            self.open_room_panel(room_number, room)
        elif room.status == "limpieza":
            if tk.messagebox.askyesno("Marcar disponible", "¿Marcar la habitación como disponible?"):
                room.set_available()
                self.update_room_status()

    def start_timer(self, room_number):
        if self.timers.get(room_number, 0) > 0:
            self.timers[room_number] -= 1
            self.update_room_status()
            self.after(1000, self.start_timer, room_number)
        else:
            room = next((r for r in self.room_manager.rooms if r.room_number == room_number), None)
            if room:
                # Verifica el saldo antes de cambiar a limpieza
                account = self.room_accounts.get(room_number, {"charges": [], "payments": [], "saldo": 0})
                base = calculate_room_price(room.hours_booked)
                cargos = sum(c["total"] for c in account["charges"] if not c.get("anulado"))
                pagos = sum(p["valor"] for p in account["payments"])
                saldo = base + cargos - pagos
                if saldo == 0:
                    room.status = "limpieza"
                else:
                    room.status = "ocupada"
                    tk.messagebox.showwarning(
                        "Saldo pendiente",
                        f"No puede pasar a limpieza. El saldo debe estar en cero.\nSaldo actual: ${saldo:.2f}"
                    )
            self.timers.pop(room_number, None)
            self.update_room_status()

    def open_inventory(self):
        win = tk.Toplevel(self)
        win.title("Inventario")

        def refresh_list():
            for row in tree.get_children():
                tree.delete(row)
            # Usa un solo cursor y asegúrate de consumir todos los resultados antes de cualquier otra consulta
            with self.conn.cursor(dictionary=True) as cursor:
                cursor.execute("SELECT id as code, nombre as name, cantidad as quantity, precio as price FROM inventario")
                productos = cursor.fetchall()
                for prod in productos:
                    tree.insert("", "end", values=(prod["code"], prod["name"], prod["quantity"], prod["price"]))

        def add_product():
            name = simpledialog.askstring("Nombre", "Nombre del producto:", parent=win)
            if not name:
                return
            try:
                quantity = int(simpledialog.askinteger("Cantidad", "Cantidad inicial:", parent=win, minvalue=0))
                price = float(simpledialog.askfloat("Precio", "Precio:", parent=win, minvalue=0))
            except Exception:
                messagebox.showerror("Error", "Datos inválidos.")
                return
            try:
                # Inserta y cierra el cursor ANTES de llamar a refresh_list
                with self.conn.cursor() as cursor:
                    cursor.execute(
                        "INSERT INTO inventario (nombre, codigo, cantidad, precio) VALUES (%s, %s, %s, %s)",
                        (name, name.lower().replace(" ", "_"), quantity, price)
                    )
                    self.conn.commit()
                messagebox.showinfo("Éxito", "Producto agregado correctamente.")
            except Exception as e:
                self.conn.rollback()
                messagebox.showerror("Error", f"No se pudo agregar el producto:\n{e}")
            refresh_list()

        def update_quantity(is_entry):
            selected = tree.focus()
            if not selected:
                messagebox.showwarning("Selecciona", "Selecciona un producto.")
                return
            code = int(tree.item(selected)["values"][0])
            try:
                amount = int(simpledialog.askinteger("Cantidad", "Cantidad:", parent=win))
                if not is_entry:
                    amount = -amount
            except Exception:
                messagebox.showerror("Error", "Cantidad inválida.")
                return
            with self.conn.cursor() as cursor:
                cursor.execute(
                    "UPDATE inventario SET cantidad = cantidad + %s WHERE id = %s",
                    (amount, code)
                )
                self.conn.commit()
            refresh_list()

        def remove_product():
            selected = tree.focus()
            if not selected:
                messagebox.showwarning("Selecciona", "Selecciona un producto.")
                return
            code = int(tree.item(selected)["values"][0])
            if messagebox.askyesno("Eliminar", "¿Eliminar este producto?"):
                with self.conn.cursor() as cursor:
                    cursor.execute("DELETE FROM inventario WHERE id = %s", (code,))
                    self.conn.commit()
                refresh_list()

        tree = ttk.Treeview(win, columns=("Código", "Nombre", "Cantidad", "Precio"), show="headings")
        for col in ("Código", "Nombre", "Cantidad", "Precio"):
            tree.heading(col, text=col)
        tree.pack(padx=10, pady=10, fill="both", expand=True)

        btn_frame = tk.Frame(win)
        btn_frame.pack(pady=5)
        tk.Button(btn_frame, text="Agregar producto", command=add_product).grid(row=0, column=0, padx=5)
        tk.Button(btn_frame, text="Entrada", command=lambda: update_quantity(True)).grid(row=0, column=1, padx=5)
        tk.Button(btn_frame, text="Salida", command=lambda: update_quantity(False)).grid(row=0, column=2, padx=5)
        tk.Button(btn_frame, text="Eliminar", command=remove_product).grid(row=0, column=3, padx=5)

        refresh_list()

    def open_room_panel(self, room_number, room):
        win = tk.Toplevel(self)
        win.title(f"Detalle Habitación {room_number}")

        if room_number not in self.room_accounts:
            self.room_accounts[room_number] = {"charges": [], "payments": [], "saldo": 0}

        # --- Costo de la habitación ---
        tk.Label(win, text="Costo de la habitación", font=("Arial", 12, "bold")).pack(pady=(10, 0))
        costo = calculate_room_price(room.hours_booked)
        tk.Label(win, text=f"${costo:.2f}", font=("Arial", 12)).pack()

        # --- Saldo ---
        saldo_var = tk.DoubleVar(value=calculate_room_price(room.hours_booked))
        self.room_accounts[room_number]["saldo"] = saldo_var.get()

        def calcular_saldo():
            # Cargar cargos y pagos desde la base de datos para el saldo actualizado
            cursor = self.conn.cursor(dictionary=True)
            try:
                # Cargos (no anulados)
                cursor.execute(
                    "SELECT SUM(total) as cargos FROM cargos WHERE habitacion_id = (SELECT id FROM habitaciones WHERE numero = %s) AND anulado = 0",
                    (room_number,)
                )
                cargos = cursor.fetchone()["cargos"] or 0
                # Pagos
                cursor.execute(
                    "SELECT SUM(valor) as pagos FROM pagos WHERE habitacion_id = (SELECT id FROM habitaciones WHERE numero = %s)",
                    (room_number,)
                )
                pagos = cursor.fetchone()["pagos"] or 0
            finally:
                cursor.close()
            base = calculate_room_price(room.hours_booked)
            saldo = base + cargos - pagos
            saldo_var.set(saldo)
            self.room_accounts[room_number]["saldo"] = saldo
            return saldo

        saldo_frame = tk.Frame(win)
        saldo_frame.pack(pady=(5, 10))
        tk.Label(saldo_frame, text="Saldo actual:", font=("Arial", 12, "bold")).pack(side="left")
        saldo_label = tk.Label(saldo_frame, textvariable=saldo_var, font=("Arial", 12))
        saldo_label.pack(side="left", padx=10)

        # --- Sección de Cargos (Consumos) ---
        tk.Label(win, text="Cargos (Consumos)", font=("Arial", 12, "bold")).pack(pady=(10, 0))
        charges_frame = tk.Frame(win)
        charges_frame.pack(padx=10, pady=5, fill="x")

        charges_table = ttk.Treeview(
            charges_frame,
            columns=("Fecha", "Producto", "Precio", "Cantidad", "Total", "Documento"),
            show="headings"
        )
        for col in ("Fecha", "Producto", "Precio", "Cantidad", "Total", "Documento"):
            charges_table.heading(col, text=col)
        charges_table.pack(side="left", fill="x", expand=True)

        def refresh_charges():
            for row in charges_table.get_children():
                charges_table.delete(row)
            cursor = self.conn.cursor(dictionary=True)
            try:
                cursor.execute(
                    "SELECT c.fecha, i.nombre as producto, c.precio, c.cantidad, c.total, c.documento "
                    "FROM cargos c JOIN inventario i ON c.producto_id = i.id "
                    "WHERE c.habitacion_id = (SELECT id FROM habitaciones WHERE numero = %s) AND c.anulado = 0",
                    (room_number,)
                )
                cargos = cursor.fetchall()
                for c in cargos:
                    charges_table.insert("", "end", values=(
                        c["fecha"], c["producto"], f"${c['precio']:.2f}", c["cantidad"], f"${c['total']:.2f}", c["documento"]
                    ))
            finally:
                cursor.close()
            calcular_saldo()  # <-- Actualiza el saldo después de refrescar cargos

        def add_charge():
            fecha = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            # Cargar productos desde la base de datos
            cursor = self.conn.cursor(dictionary=True)
            try:
                cursor.execute("SELECT id as code, nombre as name, cantidad as quantity, precio as price FROM inventario WHERE cantidad > 0")
                productos = cursor.fetchall()
            finally:
                cursor.close()
            if not productos:
                tk.messagebox.showinfo("Inventario vacío", "No hay productos en el inventario.")
                return
            prod_names = [f"{p['name']} (Stock: {p['quantity']})" for p in productos]
            prod_win = tk.Toplevel(win)
            prod_win.title("Seleccionar producto")
            tk.Label(prod_win, text="Seleccione un producto:").pack()
            prod_var = tk.StringVar(value=prod_names[0])
            prod_menu = ttk.Combobox(prod_win, textvariable=prod_var, values=prod_names, state="readonly")
            prod_menu.pack(pady=5)
            qty_var = tk.IntVar(value=1)
            tk.Label(prod_win, text="Cantidad:").pack()
            qty_entry = tk.Entry(prod_win, textvariable=qty_var)
            qty_entry.pack(pady=5)
            def confirmar():
                idx = prod_menu.current()
                producto = productos[idx]
                cantidad = qty_var.get()
                if cantidad < 1 or cantidad > producto["quantity"]:
                    tk.messagebox.showerror("Error", "Cantidad inválida o insuficiente en inventario.")
                    return
                precio = producto["price"]
                total = precio * cantidad
                documento = tk.simpledialog.askstring("Documento", "Documento asociado:", parent=win)
                # Obtener el id real de la habitación
                cursor = self.conn.cursor(dictionary=True)
                try:
                    cursor.execute("SELECT id FROM habitaciones WHERE numero = %s", (room_number,))
                    row = cursor.fetchone()
                    if not row:
                        tk.messagebox.showerror("Error", "No se encontró la habitación en la base de datos.")
                        return
                    habitacion_id = row["id"]
                finally:
                    cursor.close()
                # Insertar cargo usando el id real de la habitación
                cursor = self.conn.cursor()
                try:
                    cursor.execute(
                        "INSERT INTO cargos (habitacion_id, producto_id, fecha, precio, cantidad, total, documento, anulado) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)",
                        (habitacion_id, producto["code"], fecha, precio, cantidad, total, documento or "", False)
                    )
                    cursor.execute(
                        "UPDATE inventario SET cantidad = cantidad - %s WHERE id = %s",
                        (cantidad, producto["code"])
                    )
                    self.conn.commit()
                except Exception as e:
                    self.conn.rollback()
                    tk.messagebox.showerror("Error", f"No se pudo agregar el cargo:\n{e}")
                    return
                finally:
                    cursor.close()
                prod_win.destroy()
                refresh_charges()
            tk.Button(prod_win, text="Agregar", command=confirmar).pack(pady=5)

        def reverse_charge():
            selected = charges_table.focus()
            if not selected:
                tk.messagebox.showwarning("Selecciona", "Selecciona un cargo para reversar.")
                return
            # Obtener datos del cargo seleccionado
            values = charges_table.item(selected)["values"]
            fecha, producto, precio, cantidad, total, documento = values
            # Buscar el id del cargo y producto
            cursor = self.conn.cursor(dictionary=True)
            try:
                cursor.execute(
                    "SELECT c.id, c.producto_id FROM cargos c JOIN inventario i ON c.producto_id = i.id "
                    "WHERE c.habitacion_id = %s AND c.fecha = %s AND i.nombre = %s AND c.anulado = 0 LIMIT 1",
                    (room_number, fecha, producto)
                )
                row = cursor.fetchone()
            finally:
                cursor.close()
            if not row:
                tk.messagebox.showerror("Error", "No se encontró el cargo para reversar.")
                return
            cargo_id = row["id"]
            producto_id = row["producto_id"]
            # Anular el cargo y devolver cantidad al inventario
            cursor = self.conn.cursor()
            try:
                cursor.execute("UPDATE cargos SET anulado = 1 WHERE id = %s", (cargo_id,))
                cursor.execute("UPDATE inventario SET cantidad = cantidad + %s WHERE id = %s", (int(cantidad), producto_id))
                self.conn.commit()
            except Exception as e:
                self.conn.rollback()
                tk.messagebox.showerror("Error", f"No se pudo reversar el cargo:\n{e}")
                return
            finally:
                cursor.close()
            refresh_charges()

        charges_btn_frame = tk.Frame(charges_frame)
        charges_btn_frame.pack(side="right", fill="y")
        tk.Button(charges_btn_frame, text="Nueva Compra", command=add_charge).pack(padx=5, pady=2)
        tk.Button(charges_btn_frame, text="Hacer reversa", command=reverse_charge).pack(padx=5, pady=2)

        # --- Sección de Pagos ---
        tk.Label(win, text="Pagos", font=("Arial", 12, "bold")).pack(pady=(15, 0))
        payments_frame = tk.Frame(win)
        payments_frame.pack(padx=10, pady=5, fill="x")

        payments_table = ttk.Treeview(
            payments_frame,
            columns=("Fecha", "Valor", "Tipo de Pago", "Documento"),
            show="headings"
        )
        for col in ("Fecha", "Valor", "Tipo de Pago", "Documento"):
            payments_table.heading(col, text=col)
        payments_table.pack(side="left", fill="x", expand=True)

        def refresh_payments():
            for row in payments_table.get_children():
                payments_table.delete(row)
            cursor = self.conn.cursor(dictionary=True)
            try:
                cursor.execute(
                    "SELECT fecha, valor, tipo_pago, documento FROM pagos WHERE habitacion_id = (SELECT id FROM habitaciones WHERE numero = %s)",
                    (room_number,)
                )
                pagos = cursor.fetchall()
                for p in pagos:
                    payments_table.insert("", "end", values=(
                        p["fecha"], f"${p['valor']:.2f}", p["tipo_pago"], p["documento"]
                    ))
            finally:
                cursor.close()
            calcular_saldo()  # <-- Actualiza el saldo después de refrescar pagos

        def add_payment():
            fecha = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            valor = tk.simpledialog.askfloat("Valor", "Valor del pago:", parent=win, minvalue=0)
            if valor is None:
                return
            tipos_pago = ["Efectivo", "Consignación", "Tarjeta", "Nequi", "Daviplata", "Otro"]
            tipo_pago_win = tk.Toplevel(win)
            tipo_pago_win.title("Tipo de Pago")
            tk.Label(tipo_pago_win, text="Seleccione el tipo de pago:").pack()
            tipo_pago_var = tk.StringVar(value=tipos_pago[0])
            tipo_pago_menu = ttk.Combobox(tipo_pago_win, textvariable=tipo_pago_var, values=tipos_pago, state="readonly")
            tipo_pago_menu.pack(pady=5)
            def confirmar_pago():
                tipo_pago = tipo_pago_var.get()
                documento = tk.simpledialog.askstring("Documento", "Documento asociado:", parent=win)
                # Almacena el pago en la base de datos
                cursor = self.conn.cursor()
                cursor.execute(
                    "INSERT INTO pagos (habitacion_id, fecha, valor, tipo_pago, documento) VALUES (%s, %s, %s, %s, %s)",
                    (room_number, fecha, valor, tipo_pago, documento or "")
                )
                self.conn.commit()
                # Sumar a caja si es efectivo
                if tipo_pago.lower() == "efectivo":
                    self.caja_efectivo += valor
                tipo_pago_win.destroy()
                refresh_payments()  # Asegura que se actualice la tabla y el saldo
            tk.Button(tipo_pago_win, text="Agregar Pago", command=confirmar_pago).pack(pady=5)

        payments_btn_frame = tk.Frame(payments_frame)
        payments_btn_frame.pack(side="right", fill="y")
        tk.Button(payments_btn_frame, text="Nuevo Pago", command=add_payment).pack(padx=5, pady=2)

        refresh_charges()
        refresh_payments()

        # --- Botón para marcar limpieza solo si saldo es cero ---
        def marcar_limpieza():
            saldo = calcular_saldo()
            if saldo != 0:
                tk.messagebox.showwarning("Saldo pendiente", "No puede pasar a limpieza. El saldo debe estar en cero.")
                # Mantener el estado como ocupado explícitamente
                room.status = "ocupada"
                self.update_room_status()
                return
            room.status = "limpieza"
            self.update_room_status()
            win.destroy()

        tk.Button(win, text="Marcar como limpieza", command=marcar_limpieza).pack(pady=10)

    def save_room_changes(self, room):
        # Lógica para guardar cambios en los detalles de la habitación
        pass

    def esinventario(self):
        win = tk.Toplevel(self)
        win.title("Comparar Inventario Físico vs Sistema")

        # Obtener productos directamente de la base de datos
        cursor = self.conn.cursor(dictionary=True)
        try:
            cursor.execute("SELECT id as code, nombre as name, cantidad as quantity FROM inventario")
            productos = cursor.fetchall()
        finally:
            cursor.close()

        if not productos:
            tk.Label(win, text="No hay productos en el inventario.").pack(padx=10, pady=10)
            return

        tk.Label(win, text="Ingrese el inventario físico para cada producto:", font=("Arial", 12, "bold")).pack(pady=10)

        frame = tk.Frame(win)
        frame.pack(padx=10, pady=10)

        entries = {}
        for i, prod in enumerate(productos):
            tk.Label(frame, text=f"{prod['name']} (Sistema: {prod['quantity']})").grid(row=i, column=0, sticky="w", padx=5, pady=2)
            e = tk.Entry(frame, width=10)
            e.grid(row=i, column=1, padx=5, pady=2)
            entries[prod['code']] = (e, prod['quantity'], prod['name'])

        result_label = tk.Label(win, text="", font=("Arial", 11))
        result_label.pack(pady=10)

        def calcular_diferencias():
            lines = []
            for code, (entry, cantidad_sistema, nombre) in entries.items():
                try:
                    cantidad_fisica = int(entry.get())
                except Exception:
                    cantidad_fisica = 0
                diferencia = cantidad_fisica - cantidad_sistema
                lines.append(f"{nombre}: Sistema={cantidad_sistema}, Físico={cantidad_fisica}, Diferencia={diferencia}")
            result_label.config(text="\n".join(lines))

        tk.Button(win, text="Calcular Diferencias", command=calcular_diferencias).pack(pady=5)

    def esdinero(self):
        win = tk.Toplevel(self)
        win.title("Conteo de Dinero en Caja")

        tk.Label(win, text="Ingrese la cantidad de billetes/monedas por denominación:", font=("Arial", 12, "bold")).pack(pady=10)

        frame = tk.Frame(win)
        frame.pack(padx=10, pady=10)

        denominaciones = [100000, 50000, 20000, 10000, 5000, 2000, 1000, 500, 200, 100, 50]
        entries = {}
        for i, denom in enumerate(denominaciones):
            tk.Label(frame, text=f"${denom}").grid(row=i, column=0, sticky="w", padx=5, pady=2)
            e = tk.Entry(frame, width=10)
            e.grid(row=i, column=1, padx=5, pady=2)
            entries[denom] = e

        result_label = tk.Label(win, text="", font=("Arial", 11))
        result_label.pack(pady=10)

        def calcular_total():
            total_fisico = 0
            for denom, entry in entries.items():
                try:
                    cantidad = int(entry.get())
                except Exception:
                    cantidad = 0
                total_fisico += denom * cantidad
            diferencia = total_fisico - self.caja_efectivo
            result_label.config(
                text=f"Total físico: ${total_fisico}\n"
                     f"Total en sistema: ${self.caja_efectivo}\n"
                     f"Diferencia: ${diferencia}"
            )

        tk.Button(win, text="Calcular Total", command=calcular_total).pack(pady=5)

    def basecaja(self):
        win = tk.Toplevel(self)
        win.title("Base de Caja")
        tk.Label(win, text="Ingrese el dinero existente en la caja física:", font=("Arial", 12, "bold")).pack(pady=10)
        base_var = tk.DoubleVar(value=getattr(self, "base_caja", 0))
        entry = tk.Entry(win, textvariable=base_var)
        entry.pack(pady=5)
        def guardar_base():
            try:
                base = float(entry.get())
                self.base_caja = base
                self.caja_efectivo = base  # El dinero base es el dinero en sistema
                tk.messagebox.showinfo("Base de Caja", f"Base de caja guardada y dinero en sistema actualizado: ${self.base_caja}")
                win.destroy()
            except Exception:
                tk.messagebox.showerror("Error", "Ingrese un valor válido.")
        tk.Button(win, text="Guardar", command=guardar_base).pack(pady=5)

    def add_worker(self):
        win = tk.Toplevel(self)
        win.title("Añadir Trabajador")
        tk.Label(win, text="Nombre de usuario:", font=("Arial", 11)).pack(pady=5)
        username_var = tk.StringVar()
        tk.Entry(win, textvariable=username_var).pack(pady=5)
        tk.Label(win, text="Contraseña:", font=("Arial", 11)).pack(pady=5)
        password_var = tk.StringVar()
        tk.Entry(win, textvariable=password_var, show="*").pack(pady=5)
        tk.Label(win, text="Rol:", font=("Arial", 11)).pack(pady=5)
        role_var = tk.StringVar(value="user")
        role_frame = tk.Frame(win)
        role_frame.pack(pady=5)
        tk.Radiobutton(role_frame, text="Usuario normal", variable=role_var, value="user").pack(side="left", padx=5)
        tk.Radiobutton(role_frame, text="Administrador", variable=role_var, value="admin").pack(side="left", padx=5)

        def guardar_trabajador():
            username = username_var.get().strip()
            password = password_var.get().strip()
            role = role_var.get()
            is_admin = 1 if role == "admin" else 0
            if not username or not password:
                tk.messagebox.showerror("Error", "Debe ingresar usuario y contraseña.")
                return
            try:
                cursor = self.conn.cursor()
                cursor.execute(
                    "INSERT INTO usuarios (username, password, is_admin) VALUES (%s, %s, %s)",
                    (username, password, is_admin)
                )
                self.conn.commit()
                cursor.close()
                tk.messagebox.showinfo("Éxito", f"Trabajador '{username}' añadido como {'Administrador' if is_admin else 'Usuario normal'}.")
                win.destroy()
            except Exception as e:
                self.conn.rollback()
                tk.messagebox.showerror("Error", f"No se pudo guardar: {e}")

        tk.Button(win, text="Guardar", command=guardar_trabajador).pack(pady=10)

    def logout(self):
        if self.on_logout:
            self.on_logout()
        else:
            # Fallback: destruir la ventana principal si no hay callback
            self.master.destroy()

    def ver_movimientos_caja(self):
        win = tk.Toplevel(self)
        win.title("Movimientos de Caja")
        tk.Label(win, text="Movimientos de Caja", font=("Arial", 12, "bold")).pack(pady=10)

        import tkinter.ttk as ttk
        tree = ttk.Treeview(win, columns=("Fecha", "Tipo", "Valor", "Descripción"), show="headings")
        for col in ("Fecha", "Tipo", "Valor", "Descripción"):
            tree.heading(col, text=col)
        tree.pack(padx=10, pady=10, fill="both", expand=True)

        # Mostrar todos los pagos recibidos de la base de datos
        cursor = self.conn.cursor(dictionary=True)
        try:
            cursor.execute(
                "SELECT fecha, tipo_pago, valor, documento FROM pagos ORDER BY fecha DESC"
            )
            pagos = cursor.fetchall()
            for pago in pagos:
                tree.insert("", "end", values=(
                    pago["fecha"],
                    pago["tipo_pago"],
                    f"${pago['valor']:.2f}",
                    pago["documento"] or ""
                ))
        finally:
            cursor.close()