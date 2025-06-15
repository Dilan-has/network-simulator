import tkinter as tk
from PIL import Image, ImageTk

class Device:
    _id_counter = 0

    def __init__(self, canvas, x, y, name, image_path, app_ref):
        self.id = Device._id_counter
        Device._id_counter += 1
        self.canvas = canvas
        self.app = app_ref
        self.name = f"{name}_{self.id}"
        self.x = x
        self.y = y

        # Cargar imagen
        self.image = ImageTk.PhotoImage(Image.open(image_path).resize((50, 50)))
        self.item = canvas.create_image(x, y, image=self.image, anchor=tk.NW, tags="draggable")
        self.text = canvas.create_text(x + 25, y + 60, text=name)

        self.connections = []  # lista de líneas conectadas a este dispositivo

        # Guardar referencia de la imagen para evitar que se elimine
        self.canvas.image_refs.append(self.image)

        self.bind_events()

        self.config = {
            "ip": "",
            "mask": "",
            "gateway": ""
        }

    def bind_events(self):
        self.canvas.tag_bind(self.item, "<Button1-Motion>", self.move)
        self.canvas.tag_bind(self.text, "<Button1-Motion>", self.move)
        self.canvas.tag_bind(self.item, "<Button-1>", self.on_click)
        self.canvas.tag_bind(self.text, "<Button-1>", self.on_click)
        self.canvas.tag_bind(self.item, "<Double-1>", self.on_double_click)
        self.canvas.tag_bind(self.text, "<Double-1>", self.on_double_click)

    def on_double_click(self, event):
        self.app.open_config_window(self)

    def move(self, event):
        dx = event.x - self.x
        dy = event.y - self.y
        self.canvas.move(self.item, dx, dy)
        self.canvas.move(self.text, dx, dy)
        self.x = event.x
        self.y = event.y

        for conn in self.connections:
            if conn["from"] == self or conn["to"] == self:
                x1 = conn["from"].x + 25
                y1 = conn["from"].y + 25
                x2 = conn["to"].x + 25
                y2 = conn["to"].y + 25
                self.canvas.coords(conn["line"], x1, y1, x2, y2)

    def on_click(self, event):
        self.app.device_clicked(self)