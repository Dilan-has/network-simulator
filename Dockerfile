# Usar una imagen base oficial de Python
FROM python:3.13.4-slim

# Establecer el directorio de trabajo dentro del contenedor
WORKDIR /app

# Copiar el contenido del directorio actual al contenedor en /app
COPY . /app/

# Instalar dependencias del sistema para aplicaciones GUI.
# Esto es un ejemplo para Tkinter, que suele venir con Python.
# Si usas otra biblioteca GUI (como PyQt, Kivy, etc.),
# necesitarás instalar paquetes diferentes.
RUN apt-get update && apt-get install -y \
    tk \
    && rm -rf /var/lib/apt/lists/*

# Configurar la variable de entorno DISPLAY para la redirección X11
# Esto permite que la GUI del contenedor se muestre en tu host.
ENV DISPLAY=$DISPLAY

# Comando para ejecutar la aplicación
CMD ["python", "main.py"]
