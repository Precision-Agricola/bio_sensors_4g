# client/sensors/flow/flow.py

from machine import Pin
import config.runtime as runtime_config
from config.sensor_params import LIQUID_FLOW
import time

class PulseFlowSensor:
    def __init__(self, name="liquid_flow", signal=LIQUID_FLOW, model="YF-B1"):
        self.name = name
        self.signal = signal
        self.model = model
        self._pulse_count = 0
        self.pin = Pin(signal, Pin.IN)
        self.pin.irq(trigger=Pin.IRQ_RISING, handler=self._count_pulse)
        self.last_pulse_time = time.ticks_ms()

    def _count_pulse(self, pin):
        current_time = time.ticks_ms()
        if time.ticks_diff(current_time, self.last_pulse_time) > 1:
            self._pulse_count += 1
            self.last_pulse_time = current_time

    def _convert_to_lpm(self, pulses_per_sec):
        if self.model == "YF-B1":
            return (pulses_per_sec + 3) / 11
        elif self.model == "YF-B6":
            return pulses_per_sec / 6.6
        else:
            return None

    def read(self):
        try:
            time_factor = runtime_config.get_speed()
        except:
            time_factor = 1

        self._pulse_count = 0
        start_time = time.ticks_ms()
        interval_s = 1 / time_factor
        time.sleep(interval_s)
        
        elapsed_time_s = time.ticks_diff(time.ticks_ms(), start_time) / 1000.0

        count = self._pulse_count

        if count == 0:
            return 0.0

        pulses_per_sec = count / elapsed_time_s if elapsed_time_s > 0 else 0
        flow_lpm = self._convert_to_lpm(pulses_per_sec)

        return round(flow_lpm, 3) if flow_lpm is not None else 0.0
