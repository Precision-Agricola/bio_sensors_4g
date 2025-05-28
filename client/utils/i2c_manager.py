# utils/i2c_manager.py

from machine import Pin, SoftI2C
from config.config import I2C_SCL_PIN, I2C_SDA_PIN

_i2c = None

def get_i2c():
    global _i2c
    if _i2c is None:
        _i2c = SoftI2C(scl=Pin(I2C_SCL_PIN), sda=Pin(I2C_SDA_PIN))
    return _i2c
