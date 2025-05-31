# client/system/control/switch_control.py

from machine import Pin
import uasyncio as asyncio
from config.config import SWITCH_PIN, RECIRCULATION_POMP_PIN

switch_pin = Pin(SWITCH_PIN, Pin.IN, Pin.PULL_UP)
recirculation_pomp = Pin(RECIRCULATION_POMP_PIN, Pin.OUT)

DEBOUNCE_MS = 50
POLL_INTERVAL = 0.01  # 10 ms
STABLE_COUNT = int(DEBOUNCE_MS / (POLL_INTERVAL * 1000))

async def monitor_switch():
    last_state = switch_pin.value()
    stable_counter = 0
    pomp_on = False

    while True:
        current = switch_pin.value()

        if current != last_state:
            stable_counter = 0
        else:
            stable_counter += 1

        if stable_counter >= STABLE_COUNT:
            if current == 0 and not pomp_on:
                recirculation_pomp.on()
                pomp_on = True
            elif current == 1 and pomp_on:
                recirculation_pomp.off()
                pomp_on = False

        last_state = current
        await asyncio.sleep(POLL_INTERVAL)
