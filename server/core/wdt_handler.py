#server/wdt_handler.py

import uasyncio as asyncio
import machine
from utils.logger import log_message

WDT_TIMEOUT_MS = 8000

async def feed_watchdog_loop(wdt):
    while True:
        #TODO: implement the feed to wdt in  production
        #wdt.feed()
        await asyncio.sleep(2)

async def start_watchdog():
    try:
        #TODO: Enable wdt for production
        #wdt = machine.WDT(timeout=WDT_TIMEOUT_MS)
        wdt = None
        log_message("WDT initialized.")
        asyncio.create_task(feed_watchdog_loop(wdt))
    except Exception as e:
        log_message(f"Failed to initialize WDT: {e}")
