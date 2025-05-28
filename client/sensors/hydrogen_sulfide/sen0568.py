# client/sensors/hydrogen_sulfide/sen0568.py

from sensors.base import Sensor, register_sensor
from protocols.adc_mux import read_adc_channel 

@register_sensor("H2S", "ANALOG")
class H2SSensor(Sensor):
    def _read_implementation(self):
        return read_adc_channel(self.signal)
