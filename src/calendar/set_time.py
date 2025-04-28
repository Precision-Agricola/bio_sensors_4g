# src/calendar/set_time.py

from machine import Pin
import calendar.ds1302 as ds1302
from utils.logger import log_message

try:
    from config.config import RTC_CLK_PIN, RTC_DIO_PIN, RTC_CS_PIN
except ImportError:
    log_message("WARN: No se encontraron constantes RTC_..._PIN en config.config, usando defaults 16, 21, 23.")
    RTC_CLK_PIN = 16
    RTC_DIO_PIN = 21
    RTC_CS_PIN = 23


def init_rtc(config=None):
    clk_pin_num = RTC_CLK_PIN
    dio_pin_num = RTC_DIO_PIN
    cs_pin_num = RTC_CS_PIN

    clk = Pin(clk_pin_num)
    dio = Pin(dio_pin_num)
    cs = Pin(cs_pin_num)

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
    log_message("RTC set to:", format_datetime((year, month, day, hour, minute, 0)))

# Example usage:
# from calendar.set_time import set_current_time
# set_current_time("22/02/2025 14:19")
