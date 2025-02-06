"""NH3 analog sensor"""

from src.sensors.base import Sensor, register_sensor
from src.protocols.analog import AnalogInput
from utime import sleep_ms

@register_sensor(model="SEN0567", protocol="Analog")
class SEN0567Sensor(Sensor):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._adc = None
        self._last_raw = 0
        
    def _init_hardware(self):
        """Initialize analog input with proper configuration"""
        pin = self.config.get('pin', 34)  # Default to GPIO34 (ADC1_CH6)
        self._adc = AnalogInput(pin)
        
        # Optional: Configure moving average window
        self._window_size = self.config.get('window_size', 5)
        self._readings = [0] * self._window_size
        self._index = 0
        
        super()._init_hardware()

    def _read_implementation(self):
        """Read and process analog value"""
        try:
            raw_value = self._read_raw()
            self._update_moving_average(raw_value)
            
            return {
                'raw': raw_value,
                'average': self._last_raw,
                'voltage': raw_value * 3.3 / 4095  # ESP32 ADC resolution
            }
        except Exception as e:
            print(f"SEN0567 read error: {str(e)}")
            return None

    def _read_raw(self):
        """Perform actual ADC read with retry logic"""
        for _ in range(3):  # Max 3 retries
            value = self._adc.read()
            if 0 <= value <= 4095:
                return value
            sleep_ms(2)
        raise ValueError("Invalid ADC reading")

    def _update_moving_average(self, new_value):
        """Apply simple noise reduction"""
        self._readings[self._index] = new_value
        self._index = (self._index + 1) % self._window_size
        self._last_raw = sum(self._readings) // self._window_size
