from sensors.base import Sensor, register_sensor
from machine import UART, Pin
import time
import struct
from utils.logger import log_message

@register_sensor("RS485_SENSOR", "MODBUS")
class RS485Sensor(Sensor):
    def __init__(self, name, model, protocol, vin, signal, **kwargs):
        super().__init__(name, model, protocol, vin, signal, **kwargs)

    def _init_hardware(self):
        # UART2: TX=1, RX=3, Pull-up en RX
        # TODO: error reading sensor in OFF cycle
        Pin(3, Pin.IN, Pin.PULL_UP)  # Antes del UART 
        self.uart = UART(2, baudrate=9600, tx=1, rx=3)
        self.de_re = Pin(22, Pin.OUT)
        self.de_re.off()  # Asegura modo recepción por defecto

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

        self._initialized = True

    def _send_rs485(self, data):
        try:
            # Limpia cualquier dato previo
            self.uart.read(self.uart.any())

            self.de_re.on()
            self.uart.write(data)
            time.sleep_ms(10)
            self.de_re.off()
            time.sleep_ms(200)  # Mayor tiempo para sensores lentos

            return self.uart.read(20)
        except Exception as e:
            log_message(f"Error _send_rs485: {e}")
            return None

    def _decode_response(self, response):
        if not response or len(response) < 7:
            return None
        try:
            if (
                len(response) == 9 and
                response[0] == 0x01 and
                response[1] == 0x03 and
                response[2] == 0x04
            ):
                return struct.unpack('>f', response[3:7])[0]
            else:
                return None
        except Exception as e:
            log_message(f"Error _decode_response: {e}")
            return None

    def _get_reliable_reading(self, cmd, param_name, attempts=5, delay_ms=250):
        valid_readings = []
        raw_values = []

        for _ in range(attempts):
            response = self._send_rs485(cmd)
            value = self._decode_response(response)
            raw_values.append(value)

            if value is not None:
                min_val, max_val = self.valid_ranges.get(param_name, (-1e10, 1e10))
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

        rs485_temp = self._get_reliable_reading(self.commands[1], "rs485_temperature")
        readings["rs485_temperature"] = rs485_temp

        ambient_temp = self._get_reliable_reading(self.commands[2], "ambient_temperature")
        readings["ambient_temperature"] = ambient_temp

        return readings
