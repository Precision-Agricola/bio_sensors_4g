"""NH3 - Amonia analog sensor"""

from sensors.base import Sensor, register_sensor
from protocols.analog import AnalogInput

@register_sensor("NH3", "ANALOG")
class NH3Sensor(Sensor):
    def _init_hardware(self):
        self.analog = AnalogInput(self.signal)  # signal = pin number, e.g., 4
        self._initialized = True

    def _read_implementation(self):
        return self.analog.read()
