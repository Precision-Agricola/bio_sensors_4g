from machine import Pin
from calendar import ds1302
from config.config import load_device_config
from datetime import datetime

class RTCManager:
    """Manages RTC operations including initialization and time setting"""
    
    DEFAULT_RTC_CONFIG = {
        "clk_pin": 16,
        "dio_pin": 21,
        "cs_pin": 23
    }

    def __init__(self, config=None):
        """
        Initialize RTC manager with configuration
        
        Args:
            config (dict, optional): Custom RTC pin configuration
        """
        if config is None:
            device_config = load_device_config()
            self.rtc_config = device_config.get('rtc', self.DEFAULT_RTC_CONFIG)
        else:
            self.rtc_config = config

        # Initialize RTC
        self.ds = ds1302.DS1302(
            Pin(self.rtc_config.get('clk_pin', self.DEFAULT_RTC_CONFIG['clk_pin'])),
            Pin(self.rtc_config.get('dio_pin', self.DEFAULT_RTC_CONFIG['dio_pin'])),
            Pin(self.rtc_config.get('cs_pin', self.DEFAULT_RTC_CONFIG['cs_pin']))
        )

    def set_time(self, year=None, month=None, day=None, hour=None, minute=None, second=None):
        """
        Set RTC time components. Only updates specified components.
        
        Args:
            year (int, optional): Year to set
            month (int, optional): Month to set (1-12)
            day (int, optional): Day to set (1-31)
            hour (int, optional): Hour to set (0-23)
            minute (int, optional): Minute to set (0-59)
            second (int, optional): Second to set (0-59)
            
        Returns:
            dict: Current time after setting specified components
        """
        if year is not None:
            self.ds.year(year)
        if month is not None:
            self.ds.month(month)
        if day is not None:
            self.ds.day(day)
        if hour is not None:
            self.ds.hour(hour)
        if minute is not None:
            self.ds.minute(minute)
        if second is not None:
            self.ds.second(second)
            
        return self.get_time()

    def set_datetime(self, datetime_str):
        """
        Set RTC time using a datetime string
        
        Args:
            datetime_str (str): Datetime string in format "YYYY-MM-DD HH:MM:SS"
            
        Returns:
            dict: Current time after setting
        """
        try:
            dt = datetime.strptime(datetime_str, "%Y-%m-%d %H:%M:%S")
            return self.set_time(
                year=dt.year,
                month=dt.month,
                day=dt.day,
                hour=dt.hour,
                minute=dt.minute,
                second=dt.second
            )
        except ValueError as e:
            raise ValueError(f"Invalid datetime format. Use YYYY-MM-DD HH:MM:SS. Error: {str(e)}")

    def get_time(self):
        """
        Get current RTC time
        
        Returns:
            dict: Current time components
        """
        return {
            'year': self.ds.year(),
            'month': self.ds.month(),
            'day': self.ds.day(),
            'hour': self.ds.hour(),
            'minute': self.ds.minute(),
            'second': self.ds.second()
        }

    def format_time(self):
        """
        Get formatted time string
        
        Returns:
            str: Formatted time string
        """
        time = self.get_time()
        return (f"Date={time['month']:02d}/{time['day']:02d}/{time['year']:04d} "
                f"Time={time['hour']:02d}:{time['minute']:02d}:{time['second']:02d}")
