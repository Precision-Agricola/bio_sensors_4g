# utils/retry_loop.py
import uasyncio as asyncio

async def retry_loop(sensor_routine):
    while True:
        sensor_routine.retry_pending_data_if_needed()
        await asyncio.sleep(5)
