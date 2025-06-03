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

    def _write_data(self, cmd, data):
        self.i2c.writeto(self.addr, bytes([(cmd >> 8) & 0xFF, cmd & 0xFF]) + data)
        time.sleep_ms(2)

    def stop_periodic(self):
        self._write_cmd(0x3F86)
        time.sleep_ms(500)

    def start_periodic(self):
        self._write_cmd(0x21B1)
        time.sleep_ms(5)

    def reinit(self):
        self._write_cmd(0x3646)
        time.sleep_ms(20)

    def self_test(self):
        self._write_cmd(0x3639)
        time.sleep(10)
        result = self._read_data(0x0000, 3)
        if (result[0] << 8 | result[1]) != 0:
            raise RuntimeError("Self test failed")

    def factory_reset(self):
        self._write_cmd(0x3632)
        time.sleep_ms(1200)

    def power_down(self):
        self._write_cmd(0x36E0)

    def wake_up(self):
        self._write_cmd(0x36F6)
        time.sleep_ms(20)

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

    def measure_single_shot(self):
        self._write_cmd(0x219D)
        time.sleep(5)

    def read_single_shot(self):
        return self.read_measurement()

    def force_calibration(self, co2_ppm):
        buf = bytearray(3)
        buf[0] = (co2_ppm >> 8) & 0xFF
        buf[1] = co2_ppm & 0xFF
        buf[2] = self._crc8(buf[:2])
        self._write_data(0x362F, buf)
        time.sleep_ms(400)

    def set_auto_calibration(self, enable=True):
        val = 1 if enable else 0
        buf = bytearray(3)
        buf[0] = (val >> 8) & 0xFF
        buf[1] = val & 0xFF
        buf[2] = self._crc8(buf[:2])
        self._write_data(0x2416, buf)

    def get_auto_calibration(self):
        self._write_cmd(0x2313)
        raw = self._read_data(0x0000, 3)
        return (raw[0] << 8 | raw[1]) != 0

    def set_temp_offset(self, offset_c):
        val = int(offset_c * 65536 / 175)
        buf = bytearray(3)
        buf[0] = (val >> 8) & 0xFF
        buf[1] = val & 0xFF
        buf[2] = self._crc8(buf[:2])
        self._write_data(0x241D, buf)

    def get_temp_offset(self):
        self._write_cmd(0x2318)
        raw = self._read_data(0x0000, 3)
        return 175.0 * ((raw[0] << 8 | raw[1]) / 65536)

    def set_sensor_altitude(self, altitude_m):
        buf = bytearray(3)
        buf[0] = (altitude_m >> 8) & 0xFF
        buf[1] = altitude_m & 0xFF
        buf[2] = self._crc8(buf[:2])
        self._write_data(0x2427, buf)

    def get_sensor_altitude(self):
        self._write_cmd(0x2322)
        raw = self._read_data(0x0000, 3)
        return (raw[0] << 8) | raw[1]

    def persist_settings(self):
        self._write_cmd(0x3615)
        time.sleep_ms(800)

    def read_serial_number(self):
        raw = self._read_data(0x3682, 9)
        if self._crc8(raw[0:2]) != raw[2] or self._crc8(raw[3:5]) != raw[5] or self._crc8(raw[6:8]) != raw[8]:
            raise ValueError("Serial number CRC mismatch")
        sn = (raw[0] << 40) | (raw[1] << 32) | (raw[3] << 24) | (raw[4] << 16) | (raw[6] << 8) | raw[7]
        return sn

