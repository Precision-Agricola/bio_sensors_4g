from machine import Pin
import uasyncio as asyncio
from config.config import STATUS_LIGHT_PIN

light = Pin(STATUS_LIGHT_PIN, Pin.OUT)

_status_mode = "ok"

def set_status(mode):
    global _status_mode
    _status_mode = mode

def get_status():
    return _status_mode

async def status_loop():
    while True:
        if _status_mode == "ok":
            light.on()
            await asyncio.sleep(1)
        elif _status_mode == "warning":
            light.on()
            await asyncio.sleep(0.5)
            light.off()
            await asyncio.sleep(0.5)
        elif _status_mode == "error":
            light.on()
            await asyncio.sleep(0.1)
            light.off()
            await asyncio.sleep(0.1)
        else:
            light.off()
            await asyncio.sleep(1)
