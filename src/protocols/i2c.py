"""I2C protocol implementation"""
from machine import I2C, Pin 

class I2CDevice:
    """
    A class to represent an I2C device.
    Args:
        bus_num (int): The I2C bus number.
        address (int): The I2C address of the device.
    Attributes:
        bus (I2C): The I2C bus object.
        address (int): The I2C address of the device.
    """
    def __init__(self, bus_num, address):
        self.bus = I2C(bus_num, scl=Pin(21), sda=Pin(23))
        self.address = address

    def read_bytes(self, register, length):
        return self.bus.readfrom_mem(self.address, register, length)

    def write_bytes(self, register, data):
        self.bus.writeto_mem(self.address, register, data)
