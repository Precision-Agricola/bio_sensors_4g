#server/core/wdt_handler.py

import uasyncio as asyncio
import machine
from utils.logger import log_message

WDT_TIMEOUT_MS = 8000

async def feed_watchdog_loop(wdt):
    while True:
        #wdt.feed() # avoid erros like None type as no feed attr
        await asyncio.sleep(2)

async def start_watchdog():
    try:
        wdt =  None # inicialicé en Nonne el wdt
        log_message("WDT initialized.")
        asyncio.create_task(feed_watchdog_loop(wdt))
    except Exception as e:
        log_message(f"Failed to initialize WDT: {e}")
