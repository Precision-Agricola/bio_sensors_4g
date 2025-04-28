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

def get_current_time(rtc):
   return (rtc.year(), rtc.month(), rtc.day(),
            rtc.hour(), rtc.minute(), rtc.second())

def format_datetime(datetime_tuple):
   return "{:04d}-{:02d}-{:02d} {:02d}:{:02d}:{:02d}".format(*datetime_tuple)
