# server/utils/rtc_utils.py

import time
import random

def get_fallback_timestamp():
    base_time = time.time()
    return round(base_time + random.random(), 6)
