# client/system/uart_listener.py

import uasyncio as asyncio
import ujson
import machine
from machine import Pin
from utils.uart import uart
from utils.logger import log_message


async def uart_listener():
    log_message("UART listener activo (cliente).")
    buffer = b""

    while True:
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

                        if command_type == "reset":
                            log_message("⚠️ RESET recibido por UART. Reiniciando cliente...")
                            machine.reset()
                        else:
                            log_message(f"ℹ️ Comando UART no reconocido: {command_type}")
                    except Exception as e:
                        log_message(f"❌ Error decodificando UART: {e}")
        except Exception as e:
            log_message(f"❌ Error leyendo UART: {e}")

        await asyncio.sleep(0.1)
