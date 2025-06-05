# controller_mqtt/menu.py

import subprocess
import tkinter as tk
from tkinter import messagebox

ENDPOINT = "a1neu73ya9bcep-ats.iot.us-east-1.amazonaws.com"
CLIENT_ID = "controller-01"

def run_command(command):
    try:
        completed = subprocess.run(command, capture_output=True, text=True)
        output = completed.stdout + "\n" + completed.stderr
        messagebox.showinfo("Resultado", output)
    except Exception as e:
        messagebox.showerror("Error", str(e))

def send_update():
    device = device_entry.get().strip()
    if not device:
        messagebox.showwarning("Advertencia", "Por favor ingresa un device ID.")
        return
    command = [
        "python", "-m", "controller_mqtt.cli",
        "--endpoint", ENDPOINT,
        "--client-id", CLIENT_ID,
        "--device", device,
        "--update", "1.0.5,http://example.com/firmware.bin"
    ]
    run_command(command)

def send_reset():
    device = device_entry.get().strip()
    if not device:
        messagebox.showwarning("Advertencia", "Por favor ingresa un device ID.")
        return
    command = [
        "python", "-m", "controller_mqtt.cli",
        "--endpoint", ENDPOINT,
        "--client-id", CLIENT_ID,
        "--device", device,
        "--reset"
    ]
    run_command(command)

def send_params():
    device = device_entry.get().strip()
    if not device:
        messagebox.showwarning("Advertencia", "Por favor ingresa un device ID.")
        return
    command = [
        "python", "-m", "controller_mqtt.cli",
        "--endpoint", ENDPOINT,
        "--client-id", CLIENT_ID,
        "--device", device,
        "--params", '{"interval": 60, "threshold": 0.75}'
    ]
    run_command(command)

# GUI con Tkinter
root = tk.Tk()
root.title("Controlador MQTT")

tk.Label(root, text="Comandos MQTT para ESP32", font=("Arial", 14)).pack(pady=10)

tk.Label(root, text="Device ID:").pack()
device_entry = tk.Entry(root, width=40)
device_entry.pack(pady=5)

tk.Button(root, text="Actualizar Firmware", command=send_update, width=30).pack(pady=5)
tk.Button(root, text="Reiniciar Dispositivo", command=send_reset, width=30).pack(pady=5)
tk.Button(root, text="Enviar Parámetros", command=send_params, width=30).pack(pady=5)

root.mainloop()
