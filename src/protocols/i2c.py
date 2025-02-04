"""Protocol communication I^2C"""
from machine import I2C, Pin
import time

class I2CDevice:
    """Helper class for I2C communication"""

    def __init__(self, i2c, address):
        self.i2c = i2c
        self.address = address

    def write_command(self, cmd, value=None):
        """Write command to I2C device"""
        if value is not None:
            self.i2c.writeto(self.address, bytes([cmd, value]))
        else:
            self.i2c.writeto(self.address, bytes([cmd]))

    def read_data(self, cmd, length):
        """Read data from I2C device"""
        self.i2c.writeto(self.address, bytes([cmd]))
        return self.i2c.readfrom(self.address, length)
