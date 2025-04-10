# sensors/rs485/rs485_sensor.py

from sensors.base import Sensor, register_sensor
from machine import UART, Pin
import time
import struct

@register_sensor("RS485_SENSOR", "MODBUS")
class RS485Sensor(Sensor):
    def __init__(self, name, model, protocol, signal=None, bus_num=None, **kwargs):
        super().__init__(name, model, protocol, signal, bus_num=bus_num, **kwargs)   



    def _init_hardware(self):
        self.uart = UART(2, baudrate=9600, tx=1, rx=3)
        self.de_re = Pin(22, Pin.OUT)
        self.commands = [
            b'\x01\x03\x04\x0a\x00\x02\xE5\x39',
            b'\x01\x03\x04\x0c\x00\x02\x05\x38'
        ]
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
            return struct.unpack('>f', response[3:7])[0]
        except:
            return None

    def _read_implementation(self):
        readings = {}
        for i, cmd in enumerate(self.commands, 1):
            response = self._send_rs485(cmd)
            val = self._decode_response(response)
            readings[f"cmd{i}"] = val
        return readings
