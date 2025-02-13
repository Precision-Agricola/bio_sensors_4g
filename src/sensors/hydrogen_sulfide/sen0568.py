from src.sensors.base import Sensor, register_sensor
from src.protocols.analog import AnalogInput

@register_sensor("H2S", "ANALOG")
class H2SSensor(Sensor):
    def _init_hardware(self):
        self.analog = AnalogInput(self.signal)  # signal = pin number, e.g., 0
        self._initialized = True

    def _read_implementation(self):
        return self.analog.read()