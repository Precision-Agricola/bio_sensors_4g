"""Pressure I2C sensor (BMP3901) reducido en MicroPython"""

import time
from sensors.base import Sensor, register_sensor
from protocols.i2c import I2CDevice

# Registros del BMP3901
REG_CHIP_ID   = 0x00
REG_PWR_CTRL  = 0x1B
REG_OSR       = 0x1C
REG_ODR       = 0x1D
REG_CONFIG    = 0x1F
REG_PRESSDATA = 0x04

@register_sensor("BMP3901", "I2C")
class BMP3901Sensor(Sensor):
    def __init__(self, **config):
        self.config = config
        self.name = config.get("name", "BMP3901")
        self._initialized = False
        self.baseline = 0.0
        self.baseline_set = False
        self._init_hardware()

    def _init_hardware(self):
        bus_num = self.config.get("bus_num", 0)
        addr = self.config.get("address")
        # Convierte dirección si es string
        address = int(addr, 16) if isinstance(addr, str) else addr
        self.i2c = I2CDevice(bus_num, address)
        if not self.begin():
            raise Exception("Error al inicializar BMP3901")
        self.calibrate_baseline()
        self._initialized = True

    def begin(self):
        chip_id = self.read_register(REG_CHIP_ID)
        print("Chip ID:", hex(chip_id))
        if chip_id != 0x60:
            return False
        # Configuración básica
        self.write_register(REG_PWR_CTRL, bytes([0x33]))
        self.write_register(REG_OSR,      bytes([0x0F]))
        self.write_register(REG_ODR,      bytes([0x00]))
        self.write_register(REG_CONFIG,   bytes([0x00]))
        time.sleep(0.1)
        return True

    def read_pressure(self):
        data = self.i2c.read_bytes(REG_PRESSDATA, 3)
        if data is None or len(data) < 3:
            return None
        adc_P = (data[0] << 16) | (data[1] << 8) | data[2]
        pressure = adc_P / 1638.4  # Conversión ajustada
        if not self.baseline_set:
            self.baseline = pressure
            self.baseline_set = True
        return pressure

    def detect_air_flow(self):
        current = self.read_pressure()
        return (current is not None) and (abs(current - self.baseline) > 0.5)

    def calibrate_baseline(self):
        suma = 0.0
        n = 10
        for _ in range(n):
            p = self.read_pressure()
            if p is None:
                continue
            suma += p
            time.sleep(0.1)
        self.baseline = suma / n
        self.baseline_set = True
        print("Nueva línea base:", self.baseline)

    def write_register(self, reg, data):
        self.i2c.write_bytes(reg, data)

    def read_register(self, reg):
        data = self.i2c.read_bytes(reg, 1)
        return data[0] if data and len(data) else 0

    def _read_implementation(self):
        pressure = self.read_pressure()
        airflow = self.detect_air_flow()
        return {"pressure": pressure, "air_flow": airflow}
