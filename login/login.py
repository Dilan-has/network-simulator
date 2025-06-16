from tkinter import *
from tkinter import messagebox
from PIL import Image, ImageTk  
import os

ICON_PATH = os.path.join(os.path.dirname(__file__), "../assets/icons/")

class LoginWindow:
    def __init__(self, master):
        """Inicializa la ventana de login y sus componentes."""
        self.master = master
        self.authenticated = False
        self.master.title("Login")
        self.master.geometry("300x400")
        self.master.resizable(False, False)

        img = Image.open(ICON_PATH + "logo.png")
        img = img.resize((100, 100))
        self.logo = ImageTk.PhotoImage(img)
        self.logo_label = Label(master, image=self.logo)
        self.logo_label.pack(pady=10)

        self.username_label = Label(master, text="Usuario")
        self.username_label.pack()
        self.username_entry = Entry(master)
        self.username_entry.pack()

        self.password_label = Label(master, text="Contraseña")
        self.password_label.pack()
        self.password_entry = Entry(master, show="*")
        self.password_entry.pack()

        self.login_button = Button(master, text="Ingresar", command=self.check_login)
        self.login_button.pack(pady=10)

        self.master.bind('<Return>', self.check_login)

    def check_login(self, event=None):
        """Verifica las credenciales ingresadas por el usuario.""" 
        username = self.username_entry.get()
        password = self.password_entry.get()

        if username == "admin" and password == "admin":
            self.master.destroy()
            self.authenticated = True
        else:
            messagebox.showerror("Error", "Credenciales incorrectas")
