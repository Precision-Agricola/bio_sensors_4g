import uasyncio as asyncio
import utime
import machine
from core.access_point import AccessPointManager
from core import websocket_server
from utils.logger import log_message
from core.aws_forwarding import send_to_aws
import network

def _get_device_id():
    mac = network.WLAN().config('mac')[-3:]
    return "server_" + ''.join('{:02X}'.format(b) for b in mac)

SSID = "PrecisionAgricola"
PASSWORD = "ag2025pass"

ENABLE_SCHEDULED_REBOOT = True
REBOOT_INTERVAL_HOURS = 6
REBOOT_INTERVAL_MS = REBOOT_INTERVAL_HOURS * 60 * 60 * 1000
INITIAL_DELAY_S  = 15

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
    log_message(f"--- Application Starting ---")
    log_message(f"Waiting {INITIAL_DELAY_S} seconds before initializing Watchdog Timer...")
    log_message(">>> You can press CTRL+C in Thonny now to stop <<<")
    await asyncio.sleep(INITIAL_DELAY_S)

    try:
        websocket_server.wdt = machine.WDT(timeout=websocket_server.WDT_TIMEOUT_MS)
        log_message("Watchdog Timer Initialized.")
        asyncio.create_task(websocket_server.watchdog_feeder())
    except Exception as e:
        log_message(f"FATAL: Could not initialize Watchdog Timer: {e}")

    if ENABLE_SCHEDULED_REBOOT:
        asyncio.create_task(scheduled_reboot_task())

    log_message("Starting main application server...")
    device_id = _get_device_id()
    startup_payload = {
        "device_id": device_id,
        "timestamp": "{:04d}-{:02d}-{:02d} {:02d}:{:02d}:{:02d}".format(*utime.localtime()[:6]),
        "data": {"status": "boot"},
        "aerator_status": "UNKNOWN"
    }
    send_to_aws(startup_payload)
    await websocket_server.start_websocket_server()

try:
    asyncio.run(main())
except KeyboardInterrupt:
    log_message("Interrupted by user.")
finally:
    log_message("Application stopped.")
