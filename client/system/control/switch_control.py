# client/system/control/switch_control.py

from machine import Pin
import uasyncio as asyncio
from config.config import SWITCH_PIN, RECIRCULATION_POMP_PIN

switch_pin = Pin(SWITCH_PIN, Pin.IN, Pin.PULL_UP)
recirculation_pomp = Pin(RECIRCULATION_POMP_PIN, Pin.OUT)

POLL_INTERVAL = 0.01
DEBOUNCE_COUNT = 5

async def monitor_switch():
    last_state = switch_pin.value()
    pressed = False
    pump_on = False

    while True:
        state = switch_pin.value()

        if last_state == 1 and state == 0:
            consistent = True
            for _ in range(DEBOUNCE_COUNT):
                await asyncio.sleep(POLL_INTERVAL)
                if switch_pin.value() != 0:
                    consistent = False
                    break
            if consistent:
                pump_on = not pump_on
                recirculation_pomp.value(pump_on)

        last_state = state
        await asyncio.sleep(POLL_INTERVAL)
