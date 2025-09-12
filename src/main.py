import mysql.connector
from mysql.connector import Error
from tkinter import Tk, messagebox
from gui.main_window import MainWindow
from gui.login_window import LoginWindow
import json
import os

STATE_FILE = "room_state.json"

def save_state(room_manager, timers):
    # Guarda el estado de las habitaciones y timers en un archivo JSON
    state = []
    for room in room_manager.rooms:
        state.append({
            "room_number": room.room_number,
            "status": room.status,
            "hours_booked": room.hours_booked,
            "seconds_left": timers.get(room.room_number, 0)  # Guarda el tiempo restante
        })
    with open(STATE_FILE, "w", encoding="utf-8") as f:
        json.dump({"rooms": state}, f)

def load_state(room_manager, timers):
    # Carga el estado de las habitaciones y timers desde un archivo JSON
    if not os.path.exists(STATE_FILE):
        return
    with open(STATE_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)
    rooms_state = {r["room_number"]: r for r in data.get("rooms", [])}
    timers.clear()
    for room in room_manager.rooms:
        if room.room_number in rooms_state:
            r = rooms_state[room.room_number]
            room.status = r.get("status", "disponible")
            room.hours_booked = r.get("hours_booked", 0)
            # Restaura el tiempo restante si existe
            if "seconds_left" in r:
                timers[room.room_number] = r["seconds_left"]

def main():
    # Conexión a la base de datos MySQL
    try:
        conn = mysql.connector.connect(
            host='127.0.0.1',   # Usa solo la IP o 'localhost'
            port=3306,          # Especifica el puerto aquí
            user='root',
            password='root',
            database='motel_db'
        )
        cursor = conn.cursor()
        cursor.execute("SELECT 1")  # Prueba simple de conexión
        cursor.fetchall()           # Consume cualquier resultado pendiente
        cursor.close()              # Cierra el cursor antes de abrir otro
    except Error as e:
        messagebox.showerror("Error de conexión", f"No se pudo conectar a la base de datos:\n{e}")
        return

    root = Tk()
    root.title("Motel Room Management")
    root.geometry("400x300")

    from rooms import RoomManager
    room_manager = RoomManager(conn)

    # Registrar habitaciones en la base de datos si no existen
    cursor = conn.cursor()
    try:
        for i in range(1, 23):  # Habitaciones 1 a 22
            cursor.execute("SELECT id FROM habitaciones WHERE numero = %s", (i,))
            cursor.fetchall()  # Consume resultados pendientes
            if cursor.rowcount == 0:
                cursor.execute(
                    "INSERT INTO habitaciones (numero, estado, horas_reservadas) VALUES (%s, %s, %s)",
                    (i, "disponible", 0)
                )
        conn.commit()
    finally:
        cursor.close()

    timers = {}  # {room_number: seconds_left}
    load_state(room_manager, timers)  # <-- Cargar estado al iniciar

    def show_login():
        for widget in root.winfo_children():
            widget.destroy()
        LoginWindow(root, on_login_success, conn)  # Pasa la conexión

    def on_login_success(is_admin=False):
        for widget in root.winfo_children():
            widget.destroy()
        MainWindow(
            root,
            is_admin=is_admin,
            room_manager=room_manager,
            timers=timers,
            on_logout=show_login,
            conn=conn
        ).pack(expand=True, fill='both')

    LoginWindow(root, on_login_success, conn)  # Pasa la conexión
    try:
        root.mainloop()
    finally:
        save_state(room_manager, timers)
        conn.close()

if __name__ == "__main__":
    main()