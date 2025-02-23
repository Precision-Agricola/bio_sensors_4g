"""Implementación del protocolo I2C actualizado"""
from machine import I2C, Pin

class I2CDevice:
    """
    Clase que representa un dispositivo I2C.
    
    Args:
        bus_num (int): Número del bus I2C.
        address (int): Dirección I2C del dispositivo.
        scl_pin (int): Número de pin para SCL.
        sda_pin (int): Número de pin para SDA.
    """
    def __init__(self, bus_num, address, scl_pin=21, sda_pin=23):
        self.bus = I2C(bus_num, scl=Pin(scl_pin), sda=Pin(sda_pin))
        self.address = address

    def read_bytes(self, register, length):
        """Lee una cantidad de bytes desde un registro especificado."""
        return self.bus.readfrom_mem(self.address, register, length)

    def write_bytes(self, register, data):
        """Escribe un arreglo de bytes en el registro especificado."""
        self.bus.writeto_mem(self.address, register, data)

def init_i2c(bus_num=1, scl_pin=21, sda_pin=23):
    """
    Función de conveniencia para inicializar el bus I2C con los pines especificados.
    
    Returns:
        I2C: Objeto I2C configurado.
    """
    return I2C(bus_num, scl=Pin(scl_pin), sda=Pin(sda_pin))
