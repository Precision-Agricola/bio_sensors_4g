# client/sensors/amonia/sen0567.py

from sensors.base import Sensor, register_sensor
from protocols.adc_mux import read_adc_channel

@register_sensor("NH3", "ANALOG")
class NH3Sensor(Sensor):
    def _read_implementation(self):
        return read_adc_channel(self.signal)
