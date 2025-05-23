# server/core/uart_listener.py

import machine
import ujson
import uasyncio as asyncio
from utils.logger import log_message

uart = machine.UART(1, baudrate=9600, tx=machine.Pin(8), rx=machine.Pin(9))

async def uart_listener(sensor_routine=None):
    log_message("UART listener started.")
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
                        log_message(f"UART received: {data}")
                        if sensor_routine:
                            sensor_routine.scheduler.enqueue_from_uart(data)
                    except Exception as e:
                        log_message(f"UART read error: {e}")
        except Exception as e:
            log_message(f"UART read error: {e}")

        await asyncio.sleep(0.05)
