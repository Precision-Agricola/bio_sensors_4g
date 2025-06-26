from machine import I2C
import time

class SCD4x:
    def __init__(self, i2c, addr=0x62):
        self.i2c = i2c
        self.addr = addr

    def _crc8(self, data):
        crc = 0xFF
        for byte in data:
            crc ^= byte
            for _ in range(8):
                if crc & 0x80:
                    crc = (crc << 1) ^ 0x31
                else:
                    crc <<= 1
                crc &= 0xFF
        return crc

    def _read_data(self, cmd, length):
        self.i2c.writeto(self.addr, bytes([(cmd >> 8) & 0xFF, cmd & 0xFF]))
        time.sleep_ms(2)
        return self.i2c.readfrom(self.addr, length)

    def _write_cmd(self, cmd):
        self.i2c.writeto(self.addr, bytes([(cmd >> 8) & 0xFF, cmd & 0xFF]))
        time.sleep_ms(2)

    def stop_periodic(self):
        self._write_cmd(0x3F86)
        time.sleep_ms(500)

    def start_periodic(self):
        self._write_cmd(0x21B1)
        time.sleep_ms(5)

    def data_ready(self):
        raw = self._read_data(0xE4B8, 3)
        status = (raw[0] << 8) | raw[1]
        return (status & 0x7FF) != 0

    def read_measurement(self):
        raw = self._read_data(0xEC05, 9)

        if self._crc8(raw[0:2]) != raw[2]:
            raise ValueError("CO2 CRC mismatch")
        if self._crc8(raw[3:5]) != raw[5]:
            raise ValueError("Temp CRC mismatch")
        if self._crc8(raw[6:8]) != raw[8]:
            raise ValueError("Humidity CRC mismatch")

        co2 = (raw[0] << 8) | raw[1]
        temp = -45 + 175 * ((raw[3] << 8 | raw[4]) / 65535)
        hum = 100 * ((raw[6] << 8 | raw[7]) / 65535)
        return co2, temp, hum


