from machine import Pin
from machine import SoftI2C as I2C
from config.config import I2C_SCL_PIN, I2C_SDA_PIN

class I2CDevice:
    def __init__(self, address, scl_pin=None, sda_pin=None):
        scl = scl_pin if scl_pin is not None else I2C_SCL_PIN
        sda = sda_pin if sda_pin is not None else I2C_SDA_PIN
        
        self.bus = I2C(scl=Pin(scl), sda=Pin(sda))
        self.address = address
    
    def read_bytes(self, register, length):
        return self.bus.readfrom_mem(self.address, register, length)
    
    def write_bytes(self, register, data):
        self.bus.writeto_mem(self.address, register, data)

def init_i2c(scl_pin=None, sda_pin=None):
    scl = scl_pin if scl_pin is not None else I2C_SCL_PIN
    sda = sda_pin if sda_pin is not None else I2C_SDA_PIN
    
    return I2C(scl=Pin(scl), sda=Pin(sda))
