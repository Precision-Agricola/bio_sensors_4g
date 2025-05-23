import uasyncio as asyncio
from core.uart_listener import uart_listener
from core.wdt_handler import start_watchdog
from utils.logger import log_message

INITIAL_DELAY_S = 15
REBOOT_HOURS = 6

async def reboot_task():
    await asyncio.sleep(REBOOT_HOURS * 3600)
    log_message("Scheduled reboot triggered.")
    import machine; machine.reset()

async def main():
    log_message("Server booted. Waiting REPL window...")
    await asyncio.sleep(INITIAL_DELAY_S)

    await start_watchdog()
    asyncio.create_task(uart_listener())
    asyncio.create_task(reboot_task())

    log_message("Server ready. Listening UART and sending to AWS.")
    while True:
        await asyncio.sleep(3600)

try:
    asyncio.run(main())
except KeyboardInterrupt:
    log_message("Shutdown requested by user.")
