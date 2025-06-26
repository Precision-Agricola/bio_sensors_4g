# client/calendar/rtc_utils.py

import time
import random

def get_timestamp():
    from calendar.rtc_manager import RTCManager
    try:
        rtc = RTCManager()
        time_tuple = rtc.get_time_tuple()
        return "{:04d}-{:02d}-{:02d}T{:02d}:{:02d}:{:02d}".format(*time_tuple[:6]) if time_tuple else "RTC_READ_ERROR"
    except:
        return "RTC_UNAVAILABLE"

def get_fallback_timestamp():
    base_time = time.time()
    return round(base_time + random.random(), 6)
