# server/core/uart_commands.py

from machine import reset, UART, Pin
from utils.logger import log_message
import ujson

uart = UART(1, baudrate=9600, tx=Pin(8), rx=Pin(9))


def send_uart_command(command_type: str, payload: dict = {}):
    try:
        message = ujson.dumps({
            "command_type": command_type,
            "payload": payload
        }) + "\n"
        uart.write(message)
        log_message(f"📤 Comando UART enviado: {message.strip()}")
    except Exception as e:
        log_message(f"❌ Error enviando comando UART: {e}")
