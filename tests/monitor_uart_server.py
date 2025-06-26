from machine import UART, Pin
import _thread
import time

# UART: TX=GPIO4, RX=GPIO5
uart = UART(1, tx=Pin(4), rx=Pin(5), baudrate=9600)

def receive_loop():
    buffer = b""
    while True:
        chunk = uart.read()
        if chunk:
            buffer += chunk
            while b"\n" in buffer:
                line, buffer = buffer.split(b"\n", 1)
                try:
                    mensaje = line.decode().strip()
                    if mensaje:
                        print(f"\n📨 El cliente dijo: {mensaje}")
                        print("Ingresa mensaje para cliente: ", end="")  # restaurar prompt
                except:
                    pass
        time.sleep(0.1)

# Iniciar recepción en segundo hilo
_thread.start_new_thread(receive_loop, ())

# Envío interactivo
print("🟢 Chat UART servidor listo.")
while True:
    mensaje = input("Ingresa mensaje para cliente: ")
    uart.write(mensaje + "\n")
