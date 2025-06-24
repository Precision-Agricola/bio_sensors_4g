# client_uart.py
#
# Cliente UART para ESP32. Escucha comandos desde un servidor (ej. un Pico W),
# los procesa y envía una confirmación (ack).
#
import ujson
import time
from machine import UART, Pin

# --- Configuración del Cliente (ESP32) ---
UART_ID = 1
UART_BAUDRATE = 9600
UART_TX_PIN = 0  # Pin de transmisión del ESP32
UART_RX_PIN = 2  # Pin de recepción del ESP32

# --- Inicialización del UART ---
# Se utiliza el constructor con todos los parámetros para mayor claridad.
uart = UART(UART_ID, baudrate=UART_BAUDRATE, tx=Pin(UART_TX_PIN), rx=Pin(UART_RX_PIN))

def send_ack(status: str, payload: dict = {}):
    """
    Construye y envía un paquete de confirmación (ACK) en formato JSON.
    El paquete siempre termina con un salto de línea ('\n') para la delimitación.
    """
    try:
        # El diccionario se convierte a una cadena JSON.
        pkt = ujson.dumps({"type": "ack", "status": status, "payload": payload}) + "\n"
        print(f"   ➡️  ACK: {pkt.strip()}")
        uart.write(pkt)
    except Exception as e:
        # Imprime un error si el ACK no se puede enviar.
        print(f"   ❌ ERROR al enviar ACK: {e}")

def process_command(msg: dict):
    """
    Procesa un comando ya validado como JSON y ejecuta la acción correspondiente.
    """
    command = msg.get("command_type")
    
    if command == "reset":
        # Responde al comando de reinicio.
        send_ack("ok", {"action": "resetting device"})
        print("   ↻ Simulando reinicio del dispositivo...")
        # En una implementación real, se descomentaría la siguiente línea:
        # time.sleep(1)
        # machine.reset()

    elif command == "ping":
        # El servidor pregunta si el cliente está vivo, el cliente responde "pong".
        send_ack("ok", {"response": "pong"})

    else:
        # Si el comando no es ni "reset" ni "ping", se reporta como desconocido.
        send_ack("unknown", {"received_command": command})

def main():
    """
    Función principal que imprime la guía de conexión y entra en el bucle de escucha.
    """
    # Imprime la guía de conexión al iniciar el script.
    print("\n=== Guía de Conexión UART (Cliente: ESP32 | Servidor: Pico W) ===")
    print(f"  • ESP32 TX (Pin {UART_TX_PIN}) → Pico W RX (Pin 9)")
    print(f"  • ESP32 RX (Pin {UART_RX_PIN}) → Pico W TX (Pin 8)")
    print("  • GND               → GND")
    print("=================================================================\n")
    print(f"👂 Cliente UART listo en UART{UART_ID} (Baudrate: {UART_BAUDRATE}). Esperando comandos...")
    
    # Buffer para almacenar los datos entrantes del UART.
    buffer = b""
    
    while True:
        # Comprueba si hay datos disponibles para leer.
        if uart.any():
            # Lee los datos y los añade al buffer.
            buffer += uart.read()
            
            # Procesa el buffer mientras contenga un delimitador de fin de línea.
            while b"\n" in buffer:
                # Divide el buffer en la primera línea completa y el resto.
                line, buffer = buffer.split(b"\n", 1)
                
                # Ignora líneas vacías que podrían resultar de dobles saltos de línea.
                if not line.strip():
                    continue

                print(f"\n📥 RX: {line.decode().strip()}")
                
                try:
                    # Intenta decodificar la línea como un objeto JSON.
                    msg = ujson.loads(line)
                    # Si tiene éxito, pasa el mensaje a la función de procesamiento.
                    process_command(msg)
                except Exception as e:
                    # Si el JSON es inválido o hay otro error, envía un ACK de error.
                    print(f"   ❌ ERROR al procesar línea: {e}")
                    send_ack("error", {"err": str(e), "invalid_line": line.decode().strip()})
        
        # Pequeña pausa para evitar que el bucle consuma el 100% del CPU.
        time.sleep_ms(50)

# Punto de entrada del programa.
if __name__ == "__main__":
    main()