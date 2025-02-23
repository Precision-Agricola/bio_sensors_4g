# sensors/pressure/bmp3901.py
from sensors.base import Sensor, register_sensor
from protocols.i2c import init_i2c
from utils.micropython_bmpxxx import bmpxxx

@register_sensor("BMP3901", "i2c")
class BMP3901(Sensor):
    def _init_hardware(self):
        # Inicializa el bus I2C
        i2c = init_i2c(bus_num=self.config.get("bus_num", 1), scl_pin=23, sda_pin=21)
        try:
            self.bmp = bmpxxx.BMP390(i2c=i2c, address=int(self.config.get("address"), 16))
            self.bmp.sea_level_pressure = 1013.25
            self._initialized = True
        except Exception as e:
            print(f"Error inicializando sensor BMP3901: {e}")

    def _read_implementation(self):
        return {
            "pressure": self.bmp.pressure,
            "temperature": self.bmp.temperature
        }

