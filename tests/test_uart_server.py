# server_uart.py
#
# Servidor/Controlador UART para Raspberry Pi Pico W.
# Envía comandos a un cliente (ej. un ESP32) y verifica sus respuestas (acks).
#
import ujson
import time
from machine import UART, Pin

# --- Configuración del Servidor (Pico W) ---
UART_ID = 1
UART_BAUDRATE = 9600
UART_TX_PIN = 8  # Pin de transmisión del Pico W
UART_RX_PIN = 9  # Pin de recepción del Pico W

# --- Inicialización del UART ---
uart = UART(UART_ID, baudrate=UART_BAUDRATE, tx=Pin(UART_TX_PIN), rx=Pin(UART_RX_PIN))

def send_command(cmd: str, payload: dict = None):
    """
    Construye y envía un comando en formato JSON.
    """
    try:
        pkt = ujson.dumps({"command_type": cmd, "payload": payload or {}}) + "\n"
        print(f"\n➡️  CMD: {pkt.strip()}")
        uart.write(pkt)
    except Exception as e:
        print(f"   ❌ ERROR al enviar comando: {e}")

def wait_for_ack(timeout_s: int = 2) -> dict:
    """
    Espera y decodifica una respuesta (ACK) del cliente.
    Devuelve la respuesta como un diccionario o None si hay timeout.
    """
    start_time = time.ticks_ms()
    buffer = b""
    while time.ticks_diff(time.ticks_ms(), start_time) < (timeout_s * 1000):
        if uart.any():
            buffer += uart.read()
            if b"\n" in buffer:
                line, _ = buffer.split(b"\n", 1)
                try:
                    ack = ujson.loads(line)
                    print(f"   ⬅️  ACK: {ack}")
                    return ack
                except Exception as e:
                    print(f"   ❌ ERROR: Respuesta no es JSON válido. Recibido: {line.decode().strip()}")
                    return {"status": "error", "payload": {"err": str(e)}}
    
    print("   ⚠️  Timeout: No se recibió respuesta del cliente.")
    return None

def run_test_sequence():
    """
    Ejecuta una secuencia de comandos de prueba y verifica las respuestas.
    """
    # Imprime la guía de conexión desde la perspectiva del servidor.
    print("\n=== Guía de Conexión UART (Servidor: Pico W | Cliente: ESP32) ===")
    print(f"  • Pico W TX (Pin {UART_TX_PIN}) → ESP32 RX (Pin 2)")
    print(f"  • Pico W RX (Pin {UART_RX_PIN}) → ESP32 TX (Pin 0)")
    print("  • GND               → GND")
    print("=================================================================\n")
    print("🖥️  Servidor de pruebas listo. Iniciando secuencia...")
    
    # Bucle principal de pruebas
    while True:
        # 1. Prueba de PING
        send_command("ping")
        ack = wait_for_ack()
        if ack and ack.get("status") == "ok" and ack.get("payload", {}).get("response") == "pong":
            print("   ✅ Verificación de Ping: OK")
        else:
            print("   ❌ Verificación de Ping: FALLO")
        time.sleep(3)

        # 2. Prueba de RESET
        send_command("reset")
        ack = wait_for_ack()
        if ack and ack.get("status") == "ok" and "resetting" in ack.get("payload", {}).get("action", ""):
            print("   ✅ Verificación de Reset: OK")
        else:
            print("   ❌ Verificación de Reset: FALLO")
        time.sleep(3)

        # 3. Prueba de COMANDO DESCONOCIDO
        send_command("do_something_impossible")
        ack = wait_for_ack()
        if ack and ack.get("status") == "unknown":
            print("   ✅ Verificación de Comando Desconocido: OK")
        else:
            print("   ❌ Verificación de Comando Desconocido: FALLO")
        time.sleep(3)

# Punto de entrada del programa
if __name__ == "__main__":
    run_test_sequence()
