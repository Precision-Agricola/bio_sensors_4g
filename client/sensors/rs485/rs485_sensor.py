# sensors/rs485/rs485_sensor.py

from machine import UART, Pin
import time, struct
from utils.logger import log_message
from config.sensor_params import RS485_TX, RS485_RX, RS485_DE_RE

class RS485Sensor:
    def __init__(self):
        Pin(RS485_RX, Pin.IN, Pin.PULL_UP)
        self.uart = UART(2, baudrate=9600, tx=RS485_TX, rx=RS485_RX)
        self.de_re = Pin(RS485_DE_RE, Pin.OUT)
        self.de_re.off()

        self.commands = [
            b'\x01\x03\x04\x0a\x00\x02\xE5\x39',
            b'\x01\x03\x04\x08\x00\x02\x44\xF9',
            b'\x01\x03\x04\x0c\x00\x02\x05\x38'
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

    def _decode(self, resp):
        if not resp or len(resp) < 7: return None
        try:
            if resp[:3] == b'\x01\x03\x04':
                return struct.unpack('>f', resp[3:7])[0]
        except Exception as e:
            log_message(f"RS485 decode error: {e}")
        return None

    def _get_reading(self, cmd, param, attempts=3):
        vals = []
        for _ in range(attempts):
            val = self._decode(self._send(cmd))
            if val is not None:
                min_v, max_v = self.valid_ranges.get(param, (-1e10, 1e10))
                if min_v <= val <= max_v and abs(val) > 1e-10:
                    vals.append(val)
            time.sleep_ms(200)
        return sorted(vals)[len(vals)//2] if vals else None

    def read(self):
        return {
            "level": self._get_reading(self.commands[0], "level"),
            "rs485_temperature": self._get_reading(self.commands[1], "rs485_temperature"),
            "ambient_temperature": self._get_reading(self.commands[2], "ambient_temperature")
        }
