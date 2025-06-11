# server/main.py

import uasyncio as asyncio
from core.uart_listener import uart_listener
from core.wdt_handler import start_watchdog
from core.mqtt_listener import listen_for_commands
from utils.logger import log_message
from core.aws_forwarding import send_to_aws
from config.server_settings import REBOOT_HOURS, INITIAL_DELAY_S 
from utils.payloads import build_boot_payload, build_scheduled_reboot_payload

async def reboot_task() -> None:
    await asyncio.sleep(REBOOT_HOURS * 3600)
    log_message("Scheduled reboot triggered.")
    await send_to_aws(build_scheduled_reboot_payload())
    import machine
    machine.reset()

async def main() -> None:
    log_message("Server booted. Waiting REPL window...")
    await asyncio.sleep(INITIAL_DELAY_S)
    log_message("Starting tasks...")
    asyncio.create_task(uart_listener())
    asyncio.create_task(reboot_task())
    asyncio.create_task(listen_for_commands())
    asyncio.create_task(send_to_aws(build_boot_payload()))
    log_message("Server ready. Listening UART and sending to AWS.")
    await start_watchdog()
    while True:
        await asyncio.sleep(3600)

try:
    asyncio.run(main())
except KeyboardInterrupt:
    log_message("Shutdown requested by user.")
