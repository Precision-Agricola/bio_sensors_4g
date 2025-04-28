from system.control.relays import LoadRelay
import config.runtime as runtime_config
import time
from utils.logger import log_message


def turn_on_aerators(wdt=None):
    log_message("Initializing aerator control routine...")
    time_factor = runtime_config.get_speed()
    aerator_relays = LoadRelay()
    on_time = 3 * 3600 // time_factor
    off_time = 3 * 3600 // time_factor

    log_message(f"Starting aerator cycle: {on_time}s ON, {off_time}s OFF")

    try:
        while True:
            log_message("Aerators ON")
            aerator_relays.turn_on()

            start_time = time.time()
            while time.time() - start_time < on_time:
                if wdt:
                    wdt.feed()
                time.sleep(30)

            log_message("Aerators OFF")
            aerator_relays.turn_off()

            start_time = time.time()
            while time.time() - start_time < off_time:
                if wdt:
                    wdt.feed()
                time.sleep(30)

    except Exception as e:
        log_message(f"Error in aerator routine: {e}")
        aerator_relays.turn_off()
