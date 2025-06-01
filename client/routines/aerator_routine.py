# client/routines/aerator_3hr.py

from system.control.relays import LoadRelay
import config.runtime as runtime_config
import time
from utils.logger import log_message

def turn_on_aerators(wdt=None):
    log_message("Initializing aerator control routine...")
    tf = runtime_config.get_speed()
    relays = LoadRelay()
    cycle = 3 * 3600 // tf

    log_message(f"Starting aerator cycle: {cycle}s ON, {cycle}s OFF")

    try:
        while True:
            log_message("Aerators ON")
            relays.turn_on()
            _wait(cycle, wdt)

            log_message("Aerators OFF")
            relays.turn_off()
            _wait(cycle, wdt)

    except Exception as e:
        log_message(f"Error in aerator routine: {e}")
        relays.turn_off()

def _wait(duration, wdt):
    t0 = time.time()
    while time.time() - t0 < duration:
        if wdt: wdt.feed()
        time.sleep(30)
