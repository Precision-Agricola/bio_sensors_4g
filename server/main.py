import uasyncio as asyncio
import time
import machine
from core.access_point import AccessPointManager
from core.websocket_server import start_websocket_server, watchdog_feeder

SSID = "PrecisionAgricola"
PASSWORD = "ag2025pass"

ENABLE_SCHEDULED_REBOOT = True
REBOOT_INTERVAL_HOURS = 24
REBOOT_INTERVAL_MS = REBOOT_INTERVAL_HOURS * 60 * 60 * 1000

ap_manager = AccessPointManager(ssid=SSID, password=PASSWORD)
ap_manager.setup_access_point()

async def scheduled_reboot_task():
    """Tarea que espera REBOOT_INTERVAL_MS y luego reinicia el sistema."""
    log_message(f"Scheduled reboot task started. Reboot in approx. {REBOOT_INTERVAL_HOURS} hours.")
    await asyncio.sleep_ms(REBOOT_INTERVAL_MS)

    log_message(f"Scheduled reboot interval ({REBOOT_INTERVAL_HOURS} hours) reached. Rebooting now...")
    await asyncio.sleep(2)
    machine.reset()

async def main():
    asyncio.create_task(watchdog_feeder())

    if ENABLE_SCHEDULED_REBOOT:
        asyncio.create_task(scheduled_reboot_task())

    log_message("Starting main application server...")
    await start_websocket_server()

try:
    asyncio.run(main())
except KeyboardInterrupt:
    log_message("Interrupted by user.")
finally:
    log_message("Application stopped.")
