# sensors/ph/ph_sensor.py

from sensors.base import Sensor, register_sensor
from protocols.analog import AnalogInput
import config.runtime as runtime_config
import time

@register_sensor("PH", "ANALOG")
class PhSensor(Sensor):
    def _init_hardware(self):
        self.analog = AnalogInput(32)  # GPIO32
        self._initialized = True

    def _read_implementation(self):
        time_factor = runtime_config.get_speed()
        interval = 10 / time_factor  # tiempo total ajustado dividido en 10 muestras
        samples = []

        for _ in range(10):
            samples.append(self.analog.read())
            time.sleep(interval / 10)

        avg = sum(samples) / len(samples)
        return {"ph_value": avg}
