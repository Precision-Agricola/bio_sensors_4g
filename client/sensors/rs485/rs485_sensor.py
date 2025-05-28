# sensors/rs485/rs485_sensor.py

from machine import UART, Pin
import time
import struct
from utils.logger import log_message

class RS485Sensor:
    def __init__(self):
        Pin(3, Pin.IN, Pin.PULL_UP)
        self.uart = UART(2, baudrate=9600, tx=1, rx=3)
        self.de_re = Pin(22, Pin.OUT)
        self.de_re.off()

        self.commands = [
            b'\x01\x03\x04\x0a\x00\x02\xE5\x39',  # Level
            b'\x01\x03\x04\x08\x00\x02\x44\xF9',  # RS485 Temp
            b'\x01\x03\x04\x0c\x00\x02\x05\x38'   # Ambient Temp
        ]

        self.valid_ranges = {
            "level": (-0.1, 3.0),
            "rs485_temperature": (-10, 350),
            "ambient_temperature": (0, 50)
        }

    def _send(self, cmd):
        try:
            self.uart.read(self.uart.any())
            self.de_re.on()
            self.uart.write(cmd)
            time.sleep_ms(10)
            self.de_re.off()
            time.sleep_ms(200)
            return self.uart.read(20)
        except Exception as e:
            log_message(f"RS485 send error: {e}")
            return None

    def _decode(self, response):
        if not response or len(response) < 7:
            return None
        try:
            if len(response) == 9 and response[0] == 0x01 and response[1] == 0x03:
                return struct.unpack('>f', response[3:7])[0]
            return None
        except Exception as e:
            log_message(f"RS485 decode error: {e}")
            return None

    def _get_reading(self, cmd, param, attempts=5):
        valid = []
        for _ in range(attempts):
            val = self._decode(self._send(cmd))
            if val is not None:
                min_v, max_v = self.valid_ranges.get(param, (-1e10, 1e10))
                if min_v <= val <= max_v and abs(val) > 1e-10:
                    valid.append(val)
            time.sleep_ms(200)
        return sorted(valid)[len(valid)//2] if valid else None

    def read(self):
        return {
            "level": self._get_reading(self.commands[0], "level"),
            "rs485_temperature": self._get_reading(self.commands[1], "rs485_temperature"),
            "ambient_temperature": self._get_reading(self.commands[2], "ambient_temperature")
        }
