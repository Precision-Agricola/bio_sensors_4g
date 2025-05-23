import uasyncio as asyncio
import machine
from utils.logger import log_message

WDT_TIMEOUT_MS = 8000

async def feed_watchdog_loop(wdt):
    while True:
        wdt.feed()
        await asyncio.sleep(2)

async def start_watchdog():
    try:
        wdt = machine.WDT(timeout=WDT_TIMEOUT_MS)
        log_message("WDT initialized.")
        asyncio.create_task(feed_watchdog_loop(wdt))
    except Exception as e:
        log_message(f"Failed to initialize WDT: {e}")
