# sensors/rs485/rs485_sensor.py

from sensors.base import Sensor, register_sensor
from machine import UART, Pin
import time
import struct

@register_sensor("RS485_SENSOR", "MODBUS")
class RS485Sensor(Sensor):
    def __init__(self, name, model, protocol, vin, signal, **kwargs):
        super().__init__(name, model, protocol, vin, signal, **kwargs)

    def _init_hardware(self):
        self.uart = UART(2, baudrate=9600, tx=1, rx=3)
        self.de_re = Pin(22, Pin.OUT)
        self.commands = [
            b'\x01\x03\x04\x0a\x00\x02\xE5\x39',  # Level command
            b'\x01\x03\x04\x0c\x00\x02\x05\x38'   # Temperature command
        ]

        self.valid_ranges = {
            "level": (-0.1, 3.0),     # Level between -0.1 and 3 meters
            "temperature": (0, 50)     # Temperature between 0-50°C
        }
        self._initialized = True

    def _send_rs485(self, data):
        self.de_re.on()
        self.uart.write(data)
        time.sleep_ms(10)
        self.de_re.off()
        time.sleep_ms(100)
        return self.uart.read()

    def _decode_response(self, response):
        if not response or len(response) < 7:
            return None
        try:
            value = struct.unpack('>f', response[3:7])[0]
            return value
        except:
            return None
   
    def _get_reliable_reading(self, cmd, param_name, attempts=5, delay_ms=200):
        valid_readings = []
        
        for _ in range(attempts):
            response = self._send_rs485(cmd)
            value = self._decode_response(response)
            
            if value is not None:
                min_val, max_val = self.valid_ranges[param_name]
                if min_val <= value <= max_val and abs(value) > 1e-10:
                    valid_readings.append(value)
            
            time.sleep_ms(delay_ms)
            
        if valid_readings:
            valid_readings.sort()
            return valid_readings[len(valid_readings) // 2]
        else:
            return None
            
    def _read_implementation(self):
        readings = {}

        level = self._get_reliable_reading(self.commands[0], "level")
        readings["level"] = level

        temp = self._get_reliable_reading(self.commands[1], "temperature")
        readings["temperature"] = temp

        return readings
