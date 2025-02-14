"""NH3 - Amonia analog sensor"""

from sensors.base import Sensor, register_sensor
from protocols.analog import AnalogInput

@register_sensor("NH3", "ANALOG")
class NH3Sensor(Sensor):
    def _init_hardware(self):
        super()._init_hardware()  # Call base initialization
        self.analog = AnalogInput(self.signal)  # Initialize hardware

    def _read_implementation(self):
        return self.analog.read()
