import tkinter as tk
import os
from device import Device
import json
from tkinter import filedialog
import ipaddress

ICON_PATH = os.path.join(os.path.dirname(__file__), "../assets/icons/")


def same_subnet(ip1, ip2, mask):
    net1 = ipaddress.IPv4Network(f"{ip1}/{mask}", strict=False)
    net2 = ipaddress.IPv4Network(f"{ip2}/{mask}", strict=False)
    return net1.network_address == net2.network_address


class NetworkSimApp:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Simulador de Red")
        self.root.geometry("800x600")

        self.canvas = tk.Canvas(self.root, bg="white")
        self.canvas.pack(fill=tk.BOTH, expand=True)

        # Referencias a imágenes para que no se borren
        self.canvas.image_refs = []

        self.toolbar = tk.Frame(self.root)
        self.toolbar.pack(side=tk.TOP, fill=tk.X)

        self.add_buttons()

        # Para conectar dispositivos
        self.selected_device = None
        self.connections = []  # lista de (device1, device2)
        self.delete_mode = False

        self.log_panel = tk.Text(self.root, height=6, state='disabled', bg="#f0f0f0")
        self.log_panel.pack(fill=tk.X, side=tk.BOTTOM)

        self.graph = {}  # clave: device.name, valor: lista de vecinos

        self.devices = []

    def add_buttons(self):
        tk.Button(self.toolbar, text="Computador", command=self.add_computer).pack(side=tk.LEFT)
        tk.Button(self.toolbar, text="Router", command=self.add_router).pack(side=tk.LEFT)
        tk.Button(self.toolbar, text="Switch", command=self.add_switch).pack(side=tk.LEFT)
        tk.Button(self.toolbar, text="Eliminar conexión", command=self.delete_selected_connection).pack(side=tk.LEFT)
        tk.Button(self.toolbar, text="Enviar paquete", command=self.demo_send_packet).pack(side=tk.LEFT)
        tk.Button(self.toolbar, text="Eliminar dispositivo", command=self.toggle_delete_mode).pack(side=tk.LEFT)
        tk.Button(self.toolbar, text="Guardar red", command=self.save_network).pack(side=tk.LEFT)
        tk.Button(self.toolbar, text="Cargar red", command=self.load_network).pack(side=tk.LEFT)

    def save_network(self):
        data = {
            "devices": [],
            "connections": []
        }

        for device in self.devices:
            d = {
                "name": device.name,
                "type": device.name.split("_")[0],
                "x": device.x,
                "y": device.y,
                "config": {
                    "ip": getattr(device, "ip", ""),
                    "subnet": getattr(device, "subnet", ""),
                    "gateway": getattr(device, "gateway", ""),
                    "dns": getattr(device, "dns", ""),
                    "routing_protocol": getattr(device, "routing_protocol", ""),
                    "ports": getattr(device, "ports", ""),
                    "vlan": getattr(device, "vlan", "")
                }
            }
            data["devices"].append(d)

        for conn in self.connections:
            data["connections"].append({
                "from": conn["from"].name,
                "to": conn["to"].name
            })

        file_path = filedialog.asksaveasfilename(defaultextension=".json", filetypes=[("JSON", "*.json")])
        if file_path:
            with open(file_path, "w") as f:
                json.dump(data, f, indent=4)
            self.log(f"Red guardada en {file_path}")

    def load_network(self):
        file_path = filedialog.askopenfilename(filetypes=[("JSON", "*.json")])
        if not file_path:
            return

        with open(file_path, "r") as f:
            data = json.load(f)

        # Limpiar canvas
        for d in self.devices[:]:
            self.delete_device(d)

        # Reset contador de IDs
        from device import Device
        Device._id_counter = 0

        name_to_device = {}

        for d in data["devices"]:
            tipo = d["type"]
            x = d["x"]
            y = d["y"]
            if tipo == "PC":
                new_dev = Device(self.canvas, x, y, "PC", os.path.join(ICON_PATH, "pc.png"), self)
            elif tipo == "Router":
                new_dev = Device(self.canvas, x, y, "Router", os.path.join(ICON_PATH, "router.png"), self)
            elif tipo == "Switch":
                new_dev = Device(self.canvas, x, y, "Switch", os.path.join(ICON_PATH, "switch.png"), self)
            else:
                continue

            # Sobrescribir nombre y configuración
            new_dev.name = d["name"]
            self.canvas.itemconfig(new_dev.text, text=new_dev.name)

            cfg = d["config"]
            for attr, val in cfg.items():
                setattr(new_dev, attr, val)

            self.devices.append(new_dev)
            name_to_device[new_dev.name] = new_dev

        for conn in data["connections"]:
            d1 = name_to_device.get(conn["from"])
            d2 = name_to_device.get(conn["to"])
            if d1 and d2:
                self.connect_devices(d1, d2)

        self.log(f"Red cargada desde {file_path}")

    def toggle_delete_mode(self):
        self.delete_mode = not self.delete_mode
        if self.delete_mode:
            self.log("Modo ELIMINAR dispositivo activado. Haz clic en un dispositivo para eliminarlo.")
        else:
            self.log("Modo ELIMINAR dispositivo desactivado.")

    def demo_send_packet(self): # Enviar paquete de primer dispositivo al último agregado (o usa nombres específicos)
        if len(self.devices) >= 2:
            self.send_packet(self.devices[0].name, self.devices[-1].name)
        else:
            self.log("Se necesitan al menos dos dispositivos para enviar paquete")

    def add_computer(self):
        d = Device(self.canvas, 100, 100, "PC", os.path.join(ICON_PATH, "pc.png"), self)
        self.devices.append(d)

    def add_router(self):
        d = Device(self.canvas, 200, 100, "Router", os.path.join(ICON_PATH, "router.png"), self)
        self.devices.append(d)

    def add_switch(self):
        d = Device(self.canvas, 300, 100, "Switch", os.path.join(ICON_PATH, "switch.png"), self)
        self.devices.append(d)

    def delete_selected_connection(self):
        to_remove = [c for c in self.connections if c["selected"]]
        for conn in to_remove:
            self.canvas.delete(conn["line"])
            self.connections.remove(conn)

    def device_clicked(self, device):
        if self.delete_mode:
            self.delete_device(device)
            return

        if self.selected_device is None:
            self.selected_device = device
        else:
            if self.selected_device != device:
                self.connect_devices(self.selected_device, device)
            self.selected_device = None

    def connect_devices(self, d1, d2):
        x1 = d1.x + 25
        y1 = d1.y + 25
        x2 = d2.x + 25
        y2 = d2.y + 25

        line_id = self.canvas.create_line(
            x1, y1, x2, y2,
            fill="black", width=2,
            tags=("connection",)
        )

        self.canvas.tag_bind(line_id, "<Button-1>", self.connection_clicked)

        conn = {
            "line": line_id,
            "from": d1,
            "to": d2,
            "selected": False
        }

        self.connections.append(conn)
        d1.connections.append(conn)
        d2.connections.append(conn)

        self.log(f"Conectado: {d1.name} <--> {d2.name}")

        # Registrar conexión lógica
        self.graph.setdefault(d1.name, []).append(d2.name)
        self.graph.setdefault(d2.name, []).append(d1.name)

        # Log en consola (estructura completa)
        print("[LOGICA] Estado actual de conexiones:")
        for dev, neighbors in self.graph.items():
            print(f"  {dev} --> {neighbors}")

    def connection_clicked(self, event):
        clicked_items = self.canvas.find_withtag("current")
        if not clicked_items:
            return

        item_id = clicked_items[0]

        for conn in self.connections:
            if conn["line"] == item_id:
                # Cambiar el color para indicar selección
                if not conn["selected"]:
                    self.canvas.itemconfig(item_id, fill="red")
                    conn["selected"] = True
                else:
                    self.canvas.itemconfig(item_id, fill="black")
                    conn["selected"] = False
                break

    def log(self, message):
        self.log_panel.config(state='normal')
        self.log_panel.insert(tk.END, message + "\n")
        self.log_panel.see(tk.END)
        self.log_panel.config(state='disabled')

    def find_path(self, start_name, end_name):
        from collections import deque

        queue = deque([[start_name]])
        visited = set()

        while queue:
            path = queue.popleft()
            node = path[-1]
            if node == end_name:
                return path
            elif node not in visited:
                visited.add(node)
                neighbors = self.graph.get(node, [])
                for neighbor in neighbors:
                    new_path = list(path)
                    new_path.append(neighbor)
                    queue.append(new_path)
        return None  # si no hay camino

    def send_packet(self, start_name, end_name):
        devices_dict = {d.name: d for d in self.get_all_devices()}
        start_device = devices_dict.get(start_name)
        end_device = devices_dict.get(end_name)

        if not start_device or not end_device:
            self.log(f"Dispositivo origen o destino no encontrado")
            return

        # Validar IP en origen y destino
        if not getattr(start_device, 'ip', None) or not getattr(end_device, 'ip', None):
            self.log(f"Error: El dispositivo origen o destino no tiene IP configurada.")
            return

        # Validar máscara (ejemplo básico)
        if not getattr(start_device, 'subnet', None) or not getattr(end_device, 'subnet', None):
            self.log(f"Error: El dispositivo origen o destino no tiene máscara configurada.")
            return

        # Validar que haya camino
        path = self.find_path(start_name, end_name)
        if not path:
            self.log(f"No existe ruta de {start_name} a {end_name}")
            return

        # Validar IP configurada en todos los dispositivos del camino
        for device_name in path:
            device = devices_dict[device_name]
            if not getattr(device, 'ip', None):
                self.log(f"Error: El dispositivo {device_name} en la ruta no tiene IP configurada.")
                return

        if not same_subnet(start_device.ip, end_device.ip, end_device.subnet):
            self.log(f"Advertencia: El destino no está en la misma subred. Verifica gateway o rutas.")

        # Validar protocolos (si aplica)
        if not self.validate_routing_protocols(path):
            return

        self.log(f"Enviando paquete por ruta: {' -> '.join(path)}")

        # Animación o lógica para enviar el paquete
        x = start_device.x + 25
        y = start_device.y + 25
        packet = self.canvas.create_oval(x - 7, y - 7, x + 7, y + 7, fill="blue", tags="packet")
        self.animate_packet(packet, devices_dict, path, 0)

    def validate_routing_protocols(self, path):
        devices_dict = {d.name: d for d in self.devices}
        last_protocol = None
        for name in path:
            device = devices_dict.get(name)
            if "Router" in name:
                proto = getattr(device, 'routing_protocol', None)
                if last_protocol is None:
                    last_protocol = proto
                else:
                    if proto != last_protocol:
                        self.log(f"Error: Protocolo de enrutamiento incompatible en {name} ({proto})")
                        return False
        return True

    def animate_packet(self, packet, devices, path, index):
        if index >= len(path) - 1:
            self.canvas.delete(packet)
            self.log(f"Paquete llegó a {path[-1]}")
            return

        d1 = devices[path[index]]
        d2 = devices[path[index + 1]]

        x1, y1 = d1.x + 25, d1.y + 25
        x2, y2 = d2.x + 25, d2.y + 25

        steps = 20
        dx = (x2 - x1) / steps
        dy = (y2 - y1) / steps
        step = 0

        def step_move():
            nonlocal step
            if step < steps:
                self.canvas.move(packet, dx, dy)
                step += 1
                self.root.after(50, step_move)
            else:
                self.animate_packet(packet, devices, path, index + 1)

        self.canvas.coords(packet, x1 - 7, y1 - 7, x1 + 7, y1 + 7)
        step_move()

    def delete_device(self, device):
        # Eliminar gráficos
        self.canvas.delete(device.item)
        self.canvas.delete(device.text)

        # Eliminar conexiones visuales y lógicas relacionadas
        to_remove = []
        for conn in self.connections:
            if conn["from"] == device or conn["to"] == device:
                self.canvas.delete(conn["line"])
                to_remove.append(conn)

        for conn in to_remove:
            self.connections.remove(conn)
            # También eliminar referencias en los dispositivos conectados
            if conn in conn["from"].connections:
                conn["from"].connections.remove(conn)
            if conn in conn["to"].connections:
                conn["to"].connections.remove(conn)

        # Eliminar dispositivo de la lista y grafo
        if device in self.devices:
            self.devices.remove(device)

        if device.name in self.graph:
            # eliminar el dispositivo del grafo y de los vecinos
            neighbors = self.graph.pop(device.name)
            for neighbor in neighbors:
                if neighbor in self.graph:
                    if device.name in self.graph[neighbor]:
                        self.graph[neighbor].remove(device.name)

        self.log(f"Dispositivo {device.name} eliminado.")

        # Opcional: salir modo eliminar tras borrar uno
        self.delete_mode = False
        self.log("Modo ELIMINAR dispositivo desactivado.")

    def get_all_devices(self):
        # Devuelve una lista con todos los dispositivos en el canvas
        # Asumiendo que guardas referencias a los dispositivos en la app
        # Necesitas crear esta lista al agregar dispositivos
        devices = []
        for item in self.canvas.find_withtag("draggable"):
            # Buscar Device asociado al item? Mejor guardarlos en la app
            pass
        # Pero mejor hacer que al crear cada Device guardes referencia en self.devices
        return self.devices

    def open_config_window(self, device):
        from tkinter import Toplevel, Label, Entry, Button, StringVar, OptionMenu

        win = Toplevel(self.root)
        win.title(f"Configurar {device.name}")

        Label(win, text="Nombre / Hostname:").grid(row=0, column=0, sticky="w")
        hostname_var = StringVar(value=device.name)
        hostname_entry = Entry(win, textvariable=hostname_var)
        hostname_entry.grid(row=0, column=1)

        row = 1

        tipo = device.name.split("_")[0]

        def save():
            old_name = device.name
            device.name = hostname_var.get()
            self.canvas.itemconfig(device.text, text=device.name)

            log_msg = f"[CONFIG] {old_name} → {device.name}\n"

            if tipo == "PC":
                device.ip = ip_var.get()
                device.subnet = subnet_var.get()
                device.gateway = gateway_var.get()
                device.dns = dns_var.get()

                log_msg += f"  IP: {device.ip}\n"
                log_msg += f"  Subnet: {device.subnet}\n"
                log_msg += f"  Gateway: {device.gateway}\n"
                log_msg += f"  DNS: {device.dns}\n"

            elif tipo == "Router":
                device.ip = ip_var.get()
                device.subnet = subnet_var.get()
                device.routing_protocol = routing_var.get()

                log_msg += f"  IP interfaz: {device.ip}\n"
                log_msg += f"  Subnet: {device.subnet}\n"
                log_msg += f"  Protocolo de enrutamiento: {device.routing_protocol}\n"

            elif tipo == "Switch":
                device.ports = ports_var.get()
                device.vlan = vlan_var.get()

                log_msg += f"  Puertos: {device.ports}\n"
                log_msg += f"  VLAN: {device.vlan}\n"

            self.log(log_msg.strip())
            win.destroy()

        if tipo == "PC":
            Label(win, text="Dirección IP:").grid(row=row, column=0, sticky="w")
            ip_var = StringVar(value=getattr(device, 'ip', ''))
            Entry(win, textvariable=ip_var).grid(row=row, column=1)
            row += 1

            Label(win, text="Máscara de subred:").grid(row=row, column=0, sticky="w")
            subnet_var = StringVar(value=getattr(device, 'subnet', ''))
            Entry(win, textvariable=subnet_var).grid(row=row, column=1)
            row += 1

            Label(win, text="Gateway:").grid(row=row, column=0, sticky="w")
            gateway_var = StringVar(value=getattr(device, 'gateway', ''))
            Entry(win, textvariable=gateway_var).grid(row=row, column=1)
            row += 1

            Label(win, text="DNS:").grid(row=row, column=0, sticky="w")
            dns_var = StringVar(value=getattr(device, 'dns', ''))
            Entry(win, textvariable=dns_var).grid(row=row, column=1)
            row += 1

        elif tipo == "Router":
            Label(win, text="IP Interfaz:").grid(row=row, column=0, sticky="w")
            ip_var = StringVar(value=getattr(device, 'ip', ''))
            Entry(win, textvariable=ip_var).grid(row=row, column=1)
            row += 1

            Label(win, text="Máscara de subred:").grid(row=row, column=0, sticky="w")
            subnet_var = StringVar(value=getattr(device, 'subnet', ''))
            Entry(win, textvariable=subnet_var).grid(row=row, column=1)
            row += 1

            Label(win, text="Protocolo de enrutamiento:").grid(row=row, column=0, sticky="w")
            routing_var = StringVar(value=getattr(device, 'routing_protocol', 'RIP'))
            OptionMenu(win, routing_var, "RIP", "OSPF", "BGP").grid(row=row, column=1)
            row += 1

        elif tipo == "Switch":
            Label(win, text="Número de puertos:").grid(row=row, column=0, sticky="w")
            ports_var = StringVar(value=getattr(device, 'ports', '24'))
            Entry(win, textvariable=ports_var).grid(row=row, column=1)
            row += 1

            Label(win, text="VLAN:").grid(row=row, column=0, sticky="w")
            vlan_var = StringVar(value=getattr(device, 'vlan', '1'))
            Entry(win, textvariable=vlan_var).grid(row=row, column=1)
            row += 1

        Button(win, text="Guardar", command=save).grid(row=row, column=0, columnspan=2)

    def run(self):
        self.root.mainloop()