import uasyncio as asyncio
import ujson
import machine
import config.runtime as config
from utils.uart import uart
from utils.logger import log_message
from system.ota_update import download_and_apply_update

async def uart_listener():
    """Uart Listener"""
    wlan = config.wlan
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
                        command_type = msg.get("command_type")
                        payload = msg.get("payload", {})

                        if command_type == "ota_start":
                            ssid = payload.get("ssid")
                            password = payload.get("password")
                            if ssid and password:
                                log_message("Recibida orden de actualización OTA.")
                                asyncio.create_task(download_and_apply_update(wlan, ssid, password))
                            else:
                                log_message("Comando 'ota_start' incompleto.")
                        
                        elif command_type == "reset":
                            log_message("⚠️ RESET recibido. Reiniciando...")
                            machine.reset()
                        
                        else:
                            log_message(f"ℹ️ Comando UART no reconocido: {command_type}")
                            
                    except Exception as e:
                        log_message(f"❌ Error decodificando UART: {e}")
        except Exception as e:
            log_message(f"❌ Error leyendo UART: {e}")
