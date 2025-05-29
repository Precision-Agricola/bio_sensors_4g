# client/calendar/rtc_utils.py

def get_timestamp():
    from calendar.rtc_manager import  RTCManager
    try:
        rtc = RTCManager()
        time = rtc.get_time_tuple()
        return "{:04d}-{:02d}-{:02d}T{:02d}:{:02d}:{:02d}".format(*t[:6]) if t else "RTC_READ_ERROR"
    except:
        return "RTC_UNAVAILABLE"
