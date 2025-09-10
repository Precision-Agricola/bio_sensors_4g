# client/system/uart_listener.py
import uasyncio as asyncio
import ujson
import machine
from utils.uart import uart
from utils.logger import log_message
from system.ota_update import prepare_and_reboot

async def uart_listener():
    """Escucha comandos por UART y lanza el proceso de actualización."""
    log_message("UART listener activo (cliente).")
    buffer = b""

    while True:
        await asyncio.sleep(0.1)
        try:
            chunk = uart.read()
            if chunk:
                buffer += chunk
                while b"\n" in buffer:
                    line, buffer = buffer.split(b"\n", 1)
                    try:
                        msg = ujson.loads(line.decode().strip())
                        log_message(f"UART comando recibido: {msg}")
                        
                        if msg.get("command_type") == "ota_start":
                            payload = msg.get("payload", {})
                            ssid = payload.get('ssid')
                            password = payload.get('password')
                            
                            if ssid and password:
                                log_message("Recibida orden de actualización, llamando al preparador...")
                                prepare_and_reboot(ssid=ssid, password=password)
                            else:
                                log_message("Comando 'ota_start' incompleto.")
                                
                    except Exception as e:
                        log_message(f"Error procesando línea UART: {e}")
        except Exception as e:
            log_message(f"Error crítico en el listener UART: {e}")
