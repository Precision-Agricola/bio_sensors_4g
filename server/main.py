#server/main.py

import uasyncio as asyncio
from core.uart_listener import uart_listener
from core.wdt_handler import start_watchdog
from core.mqtt_listener import listen_for_commands
from utils.logger import log_message
from utils.rtc_utils import get_fallback_timestamp
from core.aws_forwarding import send_to_aws
from config.device_info import DEVICE_ID 

INITIAL_DELAY_S = 15
REBOOT_HOURS = 0.1 # 6 minutes

async def reboot_task():
    await asyncio.sleep(REBOOT_HOURS * 3600)
    log_message("Scheduled reboot triggered.")
    # send to aws message for programmatic reboot
    send_to_aws(
        {
            "device_id": DEVICE_ID,
            "event": "scheduled_reboot",
            "timestamp": get_fallback_timestamp()
        }
    )
    import machine; machine.reset()

async def main():
    log_message("Server booted. Waiting REPL window...")
    await asyncio.sleep(INITIAL_DELAY_S)
    log_message("Saying hello to AWS...")
    try:
        send_to_aws(
            {
                "device_id": DEVICE_ID,
                "event": "boot",
                "timestamp": get_fallback_timestamp()
                }
            )
    except Exception as e:
        log_message(f"Error sending boot message to AWS: {e}")
    log_message("Starting tasks...")
    asyncio.create_task(uart_listener())
    asyncio.create_task(reboot_task())
    asyncio.create_task(listen_for_commands())
    log_message("Server ready. Listening UART and sending to AWS.")
    await start_watchdog()
    while True:
        await asyncio.sleep(3600)

try:
    asyncio.run(main())
except KeyboardInterrupt:
    log_message("Shutdown requested by user.")
