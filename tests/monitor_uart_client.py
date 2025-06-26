from machine import UART, Pin
import _thread
import time

# UART: TX=GPIO0, RX=GPIO2
uart = UART(1, tx=Pin(0), rx=Pin(2), baudrate=9600)

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
                        print(f"\n📨 El servidor dijo: {mensaje}")
                        print("Ingresa mensaje para servidor: ", end="")  # restaurar prompt
                except:
                    pass
        time.sleep(0.1)
# Iniciar recepción en segundo hilo
_thread.start_new_thread(receive_loop, ())

# Envío interactivo
print("🟢 Chat UART cliente listo.")
while True:
    mensaje = input("Ingresa mensaje para servidor: ")
    uart.write(mensaje + "\n")
