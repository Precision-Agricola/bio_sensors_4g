#server/core/uart_listener.py

import machine
import ujson
import uasyncio as asyncio
from utils.logger import log_message
from core.aws_forwarding import send_to_aws

uart = machine.UART(1, baudrate=9600, tx=machine.Pin(8), rx=machine.Pin(9))

async def uart_listener():
    log_message("UART listener active.")
    buffer = b""

    while True:
        try:
            chunk = uart.read()
            if chunk:
                buffer += chunk
                while b"\n" in buffer:
                    line, buffer = buffer.split(b"\n", 1)
                    try:
                        data = ujson.loads(line.decode().strip())
                        log_message(f"UART data received: {data}")
                        if not send_to_aws(data):
                            log_message("Backup pending (send_to_aws failed).")
                    except Exception as e:
                        log_message(f"Decode error: {e}")
        except Exception as e:
            log_message(f"UART read error: {e}")

        await asyncio.sleep(0.05)
