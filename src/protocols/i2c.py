"""I2C protocol implementation"""
class I2CDevice:
    def __init__(self, bus_num, address):
        from machine import I2C, Pin
        self.bus = I2C(bus_num, scl=Pin(22), sda=Pin(21))
        self.address = address

    def read_bytes(self, register, length):
        return self.bus.readfrom_mem(self.address, register, length)

    def write_bytes(self, register, data):
        self.bus.writeto_mem(self.address, register, data)
