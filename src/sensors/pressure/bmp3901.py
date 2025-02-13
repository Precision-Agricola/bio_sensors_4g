"""Pressure I2C sensor"""
from sensors.base import Sensor, register_sensor
from protocols.i2c import I2CDevice
import time

@register_sensor("BMP3901", "I2C")
class BMP3901Sensor(Sensor):
    def _init_hardware(self):
        bus_num = self.config.get("bus_num", 0)
        addr = self.config.get("address")
        address = int(addr, 16) if isinstance(addr, str) else addr
        self.i2c = I2CDevice(bus_num, address)
        self.baseline_set = False
        self.baseline = 0.0
        self.last_pressure = 0.0
        if not self.begin():
            raise Exception("Error al inicializar BMP3901")
        self.calibrate_baseline()
        self._initialized = True

    def begin(self):
        chip_id = self.read_register(0x00)
        print("Chip ID:", hex(chip_id))
        if chip_id != 0x60:
            return False
        # Configuración del sensor
        self.write_register(0x1B, 0x33)  # Habilita presión y temperatura
        self.write_register(0x1C, 0x0F)  # Máximo oversample
        self.write_register(0x1D, 0x00)  # Máxima velocidad de muestreo
        self.write_register(0x1F, 0x00)  # Sin filtro IIR
        time.sleep(0.1)
        return True

    def read_pressure(self):
        data = self.i2c.read_bytes(0x04, 3)
        if not data or len(data) < 3:
            return None
        adc_P = (data[0] << 16) | (data[1] << 8) | data[2]
        pressure = adc_P / 1638.4  # Conversión ajustada
        if not self.baseline_set:
            self.baseline = pressure
            self.baseline_set = True
        self.last_pressure = pressure
        return pressure

    def detect_air_flow(self):
        current_pressure = self.read_pressure()
        if current_pressure is None:
            return False
        diff = current_pressure - self.baseline
        if abs(diff) > 0.5:
            print("Diferencia de presión:", diff, "hPa")
            return True
        return False

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

    def write_register(self, reg, value):
        self.i2c.write_bytes(reg, bytes([value]))

    def read_register(self, reg):
        data = self.i2c.read_bytes(reg, 1)
        return data[0] if data and len(data) > 0 else None

    def _read_implementation(self):
        pressure = self.read_pressure()
        airflow = self.detect_air_flow()
        return {"pressure": pressure, "air_flow": airflow}
