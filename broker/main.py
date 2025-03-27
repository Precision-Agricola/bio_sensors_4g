import uasyncio as asyncio
from core.access_point import AccessPointManager
from core.websocket_server import start_websocket_server

SSID = "PrecisionAgricola"
PASSWORD = "ag2025pass"

ap_manager = AccessPointManager(ssid=SSID, password=PASSWORD)
ap_manager.setup_access_point()

async def main():
    await start_websocket_server()

asyncio.run(main())

