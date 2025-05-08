from sensors.base import Sensor, register_sensor
from machine import Pin, SoftI2C
from utils.micropython_bmpxxx.bmpxxx import BMP390
from config.config import I2C_SCL_PIN, I2C_SDA_PIN
from utils.logger import log_message

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
        self._initialized = True

    def _read_implementation(self):
        try:
            i2c = SoftI2C(
                scl=Pin(I2C_SCL_PIN),
                sda=Pin(I2C_SDA_PIN)
            )

            found_addresses = i2c.scan()
            log_message(f"I2C scan found devices at: {[hex(addr) for addr in found_addresses]}")

            bmp_addresses = [0x76, 0x77]
            active_address = None

            for addr in bmp_addresses:
                if addr in found_addresses:
                    active_address = addr
                    log_message(f"Using BMP390 at address: 0x{addr:02x}")
                    break

            if active_address is None:
                log_message("BMP390 not found at either 0x76 or 0x77")
                return None
            bmp = BMP390(i2c=i2c, address=active_address)

            pressure = bmp.pressure
            temperature = bmp.temperature
            altitude = bmp.altitude

            return {
                "pressure": pressure,
                "temperature": temperature,
                "altitude": altitude
            }
        except Exception as e:
            log_message(f"BMP390 read error: {e}")
            return None
