from system.control.relays import LoadRelay
import config.runtime as runtime_config
import time

def turn_on_aerators(wdt=None):
    print("Initializing aerator control routine...")
    time_factor = runtime_config.get_speed()
    aerator_relays = LoadRelay()
    on_time = 3 * 3600 // time_factor
    off_time = 3 * 3600 // time_factor

    print(f"Starting aerator cycle: {on_time}s ON, {off_time}s OFF")

    try:
        while True:
            print("Aerators ON")
            aerator_relays.turn_on()

            start_time = time.time()
            while time.time() - start_time < on_time:
                if wdt:
                    wdt.feed()
                time.sleep(30)

            print("Aerators OFF")
            aerator_relays.turn_off()

            start_time = time.time()
            while time.time() - start_time < off_time:
                if wdt:
                    wdt.feed()
                time.sleep(30)

    except Exception as e:
        print(f"Error in aerator routine: {e}")
        aerator_relays.turn_off()
