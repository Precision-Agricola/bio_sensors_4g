# sensors/ph/ph_sensor.py

from protocols.analog import AnalogInput
import config.runtime as runtime_config
import time

class PHSensor:
    def __init__(self, name="Sensor pH", signal=32):
        self.name = name
        self.signal = signal
        self.analog = AnalogInput(signal)
        self.calibration_value = 111.74 # Valor de calibración para el sensor pH

    def read(self):
        try:
            time_factor = runtime_config.get_speed()
        except:
            time_factor = 1  # fallback en caso de error

        interval = 10 / time_factor
        samples = [self.analog.read() for _ in range(10)]
        time.sleep(interval)
        avg = sum(samples) / len(samples)
        avg_calibrated = round(avg / self.calibration_value, 2)
        return {"ph_value_cal": avg_calibrated}
