# protocols/adc_mux.py

from utils.ads1x15 import ADS1115
from utils.i2c_manager import get_i2c

_adc = None

def read_adc_channel(channel):
    global _adc
    if _adc is None:
        _adc = ADS1115(get_i2c())
    return _adc.read(rate=4, channel1=channel)
