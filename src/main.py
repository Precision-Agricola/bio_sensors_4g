import uasyncio as asyncio
import config.runtime as config
from routines.aerator_3hr import turn_on_aerators
from machine import WDT
from utils.logger import log_message
from utils.init import system_setup

wdt = WDT(timeout=1000 * 60 * 5)

async def feed_watchdog():
    """Task to periodically feed the watchdog"""
    while True:
        wdt.feed()
        await asyncio.sleep(5)

async def run_async_mode(sensor_routine, ws_client):
    from utils.retry_loop import retry_loop
    asyncio.create_task(feed_watchdog())
    asyncio.create_task(retry_loop(sensor_routine))
    await ws_client(sensor_routine)

def main():
    mode = config.get_mode()
    system_setup()
    log_message(f"BIO-IOT v1.2 - Mode: {mode}")
    wdt.feed()

    if mode == "PROGRAM MODE":
        log_message("Program mode active - Development interfaces enabled")

    elif mode == "DEMO MODE":
        from routines.sensor_routine import SensorRoutine
        from local_network.websocket_client import websocket_client
        import _thread

        sensor_routine = SensorRoutine()
        sensor_routine.start()
        _thread.start_new_thread(turn_on_aerators, (wdt,))
        
        # Ejecuta WebSocket + retry loop
        asyncio.run(run_async_mode(sensor_routine, websocket_client))

    elif mode == "WORKING MODE":
        from routines.sensor_routine import SensorRoutine
        from local_network.websocket_client import websocket_client
        import _thread

        sensor_routine = SensorRoutine()
        sensor_routine.start()
        _thread.start_new_thread(turn_on_aerators, (wdt,))
        
        # Ejecuta WebSocket + retry loop
        asyncio.run(run_async_mode(sensor_routine, websocket_client))

if __name__ == "__main__":
    main()
