# server/core/uart_manger.py

import uasyncio
import ujson
from core.uart_listener import uart
from utils.logger import log_message

async def send_uart_command_async(command: dict):
    """
    Construye un comando JSON, lo envía por UART de forma asíncrona
    y añade un salto de línea.
    """
    try:
        message_str = ujson.dumps(command) + '\n'
        
        log_message(f"UART TX -> Enviando comando: {message_str.strip()}")
        
        uart.write(message_str)
        
        await uasyncio.sleep_ms(50)
        
        log_message("UART TX -> Comando enviado.")
        return True
        
    except Exception as e:
        log_message(f"UART TX -> ❌ Error al enviar comando: {e}")
        return False
