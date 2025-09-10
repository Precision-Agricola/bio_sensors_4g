# client/main.py (Optimizado para no usar red)

import uasyncio as asyncio
from machine import WDT
import config.runtime as config
from utils.logger import log_message
from utils.init import system_setup
from system.uart_listener import uart_listener
from system.status.indicator import set_status

wdt = WDT(timeout=1000 * 60 * 5)

async def feed_watchdog():
    while True:
        wdt.feed()
        await asyncio.sleep(5)

async def run_async_tasks(sensor_routine):
    """Ejecuta todas las tareas asíncronas de la aplicación."""
    from utils.retry_loop import retry_loop
    from system.control.switch_control import monitor_switch
    from system.status.indicator import status_loop
    
    asyncio.create_task(feed_watchdog())
    asyncio.create_task(retry_loop(sensor_routine))
    asyncio.create_task(uart_listener())
    asyncio.create_task(monitor_switch())
    asyncio.create_task(status_loop())
    
    while True:
        await asyncio.sleep(60)

def start_application_logic():
    """Inicializa y corre la lógica principal de la aplicación."""
    from tests.system_tests import run_initial_tests
    run_initial_tests()

    from routines.sensor_routine import SensorRoutine
    import _thread
    from routines.aerator_routine import turn_on_aerators

    sensor_routine = SensorRoutine()
    sensor_routine.start()
    _thread.start_new_thread(turn_on_aerators, (wdt,))

    set_status("ok")
    log_message("Estado OK: sistema operativo")
    print("-----------------------------------")

    asyncio.run(run_async_tasks(sensor_routine))

def main():
    mode = config.get_mode()
    system_setup()
    log_message(f"BIO-IOT v1.4.0-test - Mode: {mode}")
    wdt.feed()

    if mode == "PROGRAM_MODE":
        log_message("Program mode active - Development interfaces enabled")
    elif mode in ("DEMO_MODE", "WORKING_MODE"):
        start_application_logic()

if __name__ == "__main__":
    main()
