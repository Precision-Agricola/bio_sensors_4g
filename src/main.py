import uasyncio as asyncio
import config.runtime as config
from routines.aerator_3hr import turn_on_aerators

async def run_async_mode(sensor_routine, ws_client):
    from utils.retry_loop import retry_loop
    asyncio.create_task(retry_loop(sensor_routine))
    await ws_client(sensor_routine)

def main():
    mode = config.get_mode()
    print(f"BIO-IOT v1.2 - Mode: {mode}")

    if mode == "PROGRAM MODE":
        print("Program mode active - Development interfaces enabled")

    elif mode == "DEMO MODE":
        from routines.sensor_routine import SensorRoutine
        from local_network.websocket_client import websocket_client
        import _thread

        sensor_routine = SensorRoutine()
        sensor_routine.start()
        _thread.start_new_thread(turn_on_aerators, ())
        
        # Ejecuta WebSocket + retry loop
        asyncio.run(run_async_mode(sensor_routine, websocket_client))

    elif mode == "WORKING MODE":
        from routines.sensor_routine import SensorRoutine
        from local_network.websocket_client import websocket_client
        import _thread

        sensor_routine = SensorRoutine()
        sensor_routine.start()
        _thread.start_new_thread(turn_on_aerators, ())
        
        # Ejecuta WebSocket + retry loop
        asyncio.run(run_async_mode(sensor_routine, websocket_client))

if __name__ == "__main__":
    main()
