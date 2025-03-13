"""Implementación del protocolo I2C actualizado"""
from machine import Pin
from machine import SoftI2C as I2C
from config.config import I2C_SCL_PIN, I2C_SDA_PIN

class I2CDevice:
    """
    Clase que representa un dispositivo I2C.
    
    Args:
        address (int): Dirección I2C del dispositivo.
        scl_pin (int): Número de pin para SCL. Por defecto usa I2C_SCL_PIN de config.
        sda_pin (int): Número de pin para SDA. Por defecto usa I2C_SDA_PIN de config.
    """
    def __init__(self, address, scl_pin=None, sda_pin=None):
        scl = scl_pin if scl_pin is not None else I2C_SCL_PIN
        sda = sda_pin if sda_pin is not None else I2C_SDA_PIN
        
        self.bus = I2C(scl=Pin(scl), sda=Pin(sda))
        self.address = address
    
    def read_bytes(self, register, length):
        """Lee una cantidad de bytes desde un registro especificado."""
        return self.bus.readfrom_mem(self.address, register, length)
    
    def write_bytes(self, register, data):
        """Escribe un arreglo de bytes en el registro especificado."""
        self.bus.writeto_mem(self.address, register, data)

def init_i2c(scl_pin=None, sda_pin=None):
    """
    Función de conveniencia para inicializar el bus I2C con los pines especificados.
    Si no se especifican, se usan los valores de config.
    
    Returns:
        I2C: Objeto I2C configurado.
    """
    scl = scl_pin if scl_pin is not None else I2C_SCL_PIN
    sda = sda_pin if sda_pin is not None else I2C_SDA_PIN
    
    return I2C(scl=Pin(scl), sda=Pin(sda))
