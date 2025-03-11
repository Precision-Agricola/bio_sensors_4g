from machine import Pin
import calendar.ds1302 as ds1302
from config.config import load_device_config

DEFAULT_RTC_CONFIG = {
    "clk_pin": 16,
    "dio_pin": 21,
    "cs_pin": 23
}

def init_rtc(config=None):
    if config is None:
        device_config = load_device_config()
        rtc_config = device_config.get('rtc', DEFAULT_RTC_CONFIG)
    else:
        rtc_config = config
    clk = Pin(rtc_config.get('clk_pin', DEFAULT_RTC_CONFIG['clk_pin']))
    dio = Pin(rtc_config.get('dio_pin', DEFAULT_RTC_CONFIG['dio_pin']))
    cs = Pin(rtc_config.get('cs_pin', DEFAULT_RTC_CONFIG['cs_pin']))
    return ds1302.DS1302(clk, dio, cs)

def compute_weekday(day, month, year):
    if month < 3:
        month += 12
        year -= 1
    K = year % 100
    J = year // 100
    h = (day + (13 * (month + 1)) // 5 + K + K // 4 + J // 4 + 5 * J) % 7
    return ((h + 5) % 7) + 1

def format_datetime(dt):
    return "{:04d}-{:02d}-{:02d} {:02d}:{:02d}:{:02d}".format(*dt)

def set_current_time(time_str, config=None):
    """
    Set the DS1302 RTC time.
    Expects time_str in "DD/MM/YYYY HH:MM" format.
    """
    rtc = init_rtc(config)
    date_part, time_part = time_str.split(' ')
    day, month, year = map(int, date_part.split('/'))
    hour, minute = map(int, time_part.split(':'))
    weekday = compute_weekday(day, month, year)
    dt = (year, month, day, weekday, hour, minute, 0)
    rtc.date_time(dt)
    print("RTC set to:", format_datetime((year, month, day, hour, minute, 0)))

# Example usage:
# from calendar.set_time import set_current_time
# set_current_time("22/02/2025 14:19")
