import tkinter as tk
from login.login import LoginWindow
from gui.canvas_gui import NetworkSimApp

if __name__ == "__main__":
    root = tk.Tk()
    login_window = LoginWindow(root)
    root.mainloop()

    if login_window.authenticated:
        app = NetworkSimApp()
        app.run()
