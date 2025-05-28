# sensors/ph/ph_sensor.py

from protocols.analog import AnalogInput
import config.runtime as runtime_config
import time

class PHSensor:
    def __init__(self, signal=32):
        self.analog = AnalogInput(signal)

    def read(self):
        time_factor = runtime_config.get_speed()
        interval = 10 / time_factor
        samples = [self.analog.read() for _ in range(10)]
        time.sleep(interval)
        avg = sum(samples) / len(samples)
        return {"ph_value": avg}
