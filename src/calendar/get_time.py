from machine import Pin
import calendar.ds1302 as ds1302 
from config.config import load_device_config

# Define default RTC pins in case config fails
DEFAULT_RTC_CONFIG = {
    "clk_pin": 16,
    "dio_pin": 21,
    "cs_pin": 23
}

def init_rtc(config=None):
    """
    Initialize the DS1302 RTC module.
    
    Args:
        config (dict, optional): Configuration dictionary containing RTC pin assignments.
            If None, will attempt to load from device_config.json
    
    Returns:
        DS1302: Initialized RTC object
    """
    if config is None:
        device_config = load_device_config()
        rtc_config = device_config.get('rtc', DEFAULT_RTC_CONFIG)
    else:
        rtc_config = config
    
    # Create Pin objects using configuration
    clk = Pin(rtc_config.get('clk_pin', DEFAULT_RTC_CONFIG['clk_pin']))
    dio = Pin(rtc_config.get('dio_pin', DEFAULT_RTC_CONFIG['dio_pin']))
    cs = Pin(rtc_config.get('cs_pin', DEFAULT_RTC_CONFIG['cs_pin']))
    
    return ds1302.DS1302(clk, dio, cs)

def get_current_time(rtc):
    """
    Get current date and time from RTC.
    
    Args:
        rtc (DS1302): Initialized RTC object
    
    Returns:
        tuple: (year, month, day, hour, minute, second)
    """
    return (rtc.year(), rtc.month(), rtc.day(),
            rtc.hour(), rtc.minute(), rtc.second())

def format_datetime(datetime_tuple):
    """
    Format the datetime tuple into a human-readable string.
    
    Args:
        datetime_tuple (tuple): (year, month, day, hour, minute, second)
    
    Returns:
        str: Formatted datetime string (YYYY-MM-DD HH:MM:SS)
    """
    return "{:04d}-{:02d}-{:02d} {:02d}:{:02d}:{:02d}".format(*datetime_tuple)
