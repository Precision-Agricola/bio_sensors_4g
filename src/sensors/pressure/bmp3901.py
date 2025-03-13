# sensors/pressure/bmp3901.py
from sensors.base import Sensor, register_sensor
from machine import Pin, SoftI2C
from utils.micropython_bmpxxx.bmpxxx import BMP390
from config.config import I2C_SCL_PIN, I2C_SDA_PIN

@register_sensor("BMP3901", "I2C")
class BMP3901Sensor(Sensor):
    def __init__(self, name, model, protocol, vin, bus_num, address, **kwargs):
        if 'signal' not in kwargs:
            kwargs['signal'] = 0
            
        self.bus_num = bus_num
        self.address_str = address
        self.address = int(address, 16)
        super().__init__(name, model, protocol, vin, **kwargs)
    
    def _init_hardware(self):
        super()._init_hardware()
        # No inicializamos el sensor aquí, lo haremos en read_implementation
        # Solo marcamos como inicializado para que read() intente leer
        self._initialized = True
    
    def _read_implementation(self):
        try:
            # Crear el bus I2C directamente (como en tu script de prueba)
            i2c = SoftI2C(
                scl=Pin(I2C_SCL_PIN),
                sda=Pin(I2C_SDA_PIN)
            )
            
            # Verificar si el dispositivo está disponible
            found_addresses = i2c.scan()
            if self.address not in found_addresses:
                print(f"BMP3901: No se encontró dispositivo en 0x{self.address:02x}")
                print(f"Direcciones encontradas: {[hex(addr) for addr in found_addresses]}")
                return None
            
            # Crear instancia BMP390 y leer datos
            bmp = BMP390(i2c=i2c, address=self.address)
            pressure = bmp.pressure
            temperature = bmp.temperature
            altitude = bmp.altitude
            
            return {
                "pressure": pressure,
                "temperature": temperature,
                "altitude": altitude
            }
        except Exception as e:
            print(f"Error leyendo BMP3901: {str(e)}")
            return None
