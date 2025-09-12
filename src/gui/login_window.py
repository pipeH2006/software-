from tkinter import Tk, Label, Entry, Button, StringVar, messagebox
from auth import login

class LoginWindow:
    def __init__(self, master, on_login_success, conn=None):
        self.master = master
        self.conn = conn
        master.title("Login")

        self.username_label = Label(master, text="Username:")
        self.username_label.pack()

        self.username = StringVar()
        self.username_entry = Entry(master, textvariable=self.username)
        self.username_entry.pack()

        self.password_label = Label(master, text="Password:")
        self.password_label.pack()

        self.password = StringVar()
        self.password_entry = Entry(master, textvariable=self.password, show='*')
        self.password_entry.pack()

        # Añadir botón de login
        self.login_button = Button(master, text="Login", command=self.authenticate)
        self.login_button.pack()

        self.on_login_success = on_login_success

    def authenticate(self):
        username = self.username.get()
        password = self.password.get()
        # Pasa la conexión a login
        ok, is_admin = login(username, password, self.conn)
        if ok:
            self.on_login_success(is_admin)
        else:
            messagebox.showerror("Login Failed", "Invalid username or password.")