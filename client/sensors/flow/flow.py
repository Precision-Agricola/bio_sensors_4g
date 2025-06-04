# client/sensors/flow/flow.py

from machine import Pin
import config.runtime as runtime_config
from config.sensor_params import LIQUID_FLOW
import time

class PulseFlowSensor:
    def __init__(self, name="Flujo Agua YF-B1", signal=LIQUID_FLOW, model="YF-B1"):
        self.name = name
        self.signal = signal
        self.model = model
        self._pulse_count = 0
        self.pin = Pin(signal, Pin.IN)
        self.pin.irq(trigger=Pin.IRQ_RISING, handler=self._count_pulse)

    def _count_pulse(self, pin):
        self._pulse_count += 1

    def _convert_to_lpm(self, pulses_per_sec):
        if self.model == "YF-B1":
            return (pulses_per_sec + 3) / 11  # F = 11Q - 3 → Q = (F + 3) / 11
        elif self.model == "YF-B6":
            return pulses_per_sec / 6.6       # F = 6.6Q → Q = F / 6.6
        else:
            return None

    def read(self):
        try:
            time_factor = runtime_config.get_speed()
        except:
            time_factor = 1

        self._pulse_count = 0
        interval = 1 / time_factor  # segundos reales simulados
        time.sleep(interval)
        count = self._pulse_count
        flow_lpm = self._convert_to_lpm(count / interval)
        return {
            "pulse_count": count,
            "flow_lpm": round(flow_lpm, 3) if flow_lpm is not None else None,
            "model": self.model
        }
