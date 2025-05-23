import uasyncio as asyncio
from machine import WDT
import config.runtime as config
from utils.logger import log_message
from utils.init import system_setup

wdt = WDT(timeout=1000 * 60 * 5)

async def feed_watchdog():
    while True:
        wdt.feed()
        await asyncio.sleep(5)

async def run_async_mode(sensor_routine):
    from utils.retry_loop import retry_loop
    asyncio.create_task(feed_watchdog())
    asyncio.create_task(retry_loop(sensor_routine))
    while True:
        await asyncio.sleep(60)

def start_sensor_cycle():
    from tests.system_tests import run_initial_tests
    run_initial_tests()

    from routines.sensor_routine import SensorRoutine
    import _thread
    from routines.aerator_3hr import turn_on_aerators

    sensor_routine = SensorRoutine()
    sensor_routine.start()
    _thread.start_new_thread(turn_on_aerators, (wdt,))
    asyncio.run(run_async_mode(sensor_routine))

def main():
    mode = config.get_mode()
    system_setup()
    log_message(f"BIO-IOT v1.2 - Mode: {mode}")
    wdt.feed()

    if mode == "PROGRAM MODE":
        log_message("Program mode active - Development interfaces enabled")
    elif mode in ("DEMO MODE", "WORKING MODE"):
        start_sensor_cycle()

if __name__ == "__main__":
    main()
