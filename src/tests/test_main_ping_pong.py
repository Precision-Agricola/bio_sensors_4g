# src/main.py
import uasyncio as asyncio
import _thread
from local_network.wifi import connect_wifi
from routines.sensor_routine import SensorRoutine
from routines.aerator_3hrs import turn_on_aerators
from utils.connection_manager import ConnectionManager

async def connection_heartbeat(conn_manager):
    """Periodically ping the server to keep the connection alive."""
    while True:
        if not conn_manager.connected:
            print("Heartbeat: Attempting to connect...")
            await conn_manager.connect()
        else:
            try:
                await conn_manager.send("PING")
            except Exception as e:
                print("Heartbeat error:", e)
        await asyncio.sleep(30)  # Check every 30 seconds

async def main_async():
    conn_manager = ConnectionManager(uri="ws://192.168.4.1/ws")
    # Run the connection manager's run loop and heartbeat concurrently.
    asyncio.create_task(conn_manager.run())
    asyncio.create_task(connection_heartbeat(conn_manager))
    while True:
        await asyncio.sleep(3600)  # Keep the loop alive

def main():
    if not connect_wifi():
        print("WiFi not connected. Exiting...")
        return

    # Start sensor routine (runs in its own thread via scheduler)
    sensor_routine = SensorRoutine()
    sensor_routine.start()

    # Run aerator cycle in a separate thread to avoid blocking
    _thread.start_new_thread(turn_on_aerators, ())

    try:
        asyncio.run(main_async())
    except Exception as e:
        print("Error running asyncio loop:", e)

if __name__ == "__main__":
    main()
