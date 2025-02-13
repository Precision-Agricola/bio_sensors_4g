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
        """Reads a specified number of bytes from a register on the I2C device.
            Args:
                register (int): The register address to read from.
                length (int): The number of bytes to read.
            Returns:
                bytes: The bytes read from the register.
            """

        return self.bus.readfrom_mem(self.address, register, length)

    def write_bytes(self, register, data):
        """Writes a byte array to the specified register.
            Args:
                register (int): The register to write to.
                data (bytes): The byte array to write.
            """
        self.bus.writeto_mem(self.address, register, data)
