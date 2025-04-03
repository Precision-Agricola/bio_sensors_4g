"""
Presición Agrícola -- BioReactores IoT

Caleb de la Vara
Raúl Venegas
Eduardo Santos

April 2025
"""
import uasyncio as asyncio
from core.access_point import AccessPointManager
from core.websocket_server import start_websocket_server, watchdog_feeder
from core.aws_forwarding import retry_pending_data

SSID = "PrecisionAgricola"
PASSWORD = "ag2025pass"

ap_manager = AccessPointManager(ssid=SSID, password=PASSWORD)

async def retry_pending_data_task():
    while True:
        retry_pending_data()
        await asyncio.sleep(300)


async def main():
    await ap_manager.setup_access_point()
    asyncio.create_task(watchdog_feeder())
    asyncio.create_task(retry_pending_data_task())
    await start_websocket_server()

asyncio.run(main())
