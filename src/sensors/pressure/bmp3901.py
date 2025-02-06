"""Pressure I2C sensor"""
from src.sensors.base import Sensor, register_sensor
from src.protocols.i2c import I2CDevice
from utime import sleep_ms

@register_sensor
class BMP390LSensor(Sensor):
    # Sensor constants
    _REG_CHIP_ID = 0x00
    _REG_STATUS = 0x03
    _REG_DATA = 0x04  # Pressure + Temperature (6 bytes)
    _REG_CTRL_MEAS = 0x1B
    _REG_CALIBRATION = 0x31  # Calibration data (21 bytes)
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._i2c = None
        self._calibration = {}

    def _init_hardware(self):
        """Initialize sensor and load calibration data"""
        address = self.config.get('address', 0x77)
        bus = self.config.get('bus', 0)
        self._i2c = I2CDevice(bus, address)
        
        # Verify chip ID
        chip_id = self._read_register(self._REG_CHIP_ID, 1)[0]
        if chip_id != 0x60:
            raise RuntimeError(f"Invalid BMP390L chip ID: 0x{chip_id:02x}")
        
        self._load_calibration()
        self._configure_sensor()
        super()._init_hardware()

    def _read_register(self, reg, length):
        """Generic register read using I2C protocol"""
        return self._i2c.read_bytes(reg, length)

    def _load_calibration(self):
        """Load and parse calibration coefficients"""
        calib = self._read_register(self._REG_CALIBRATION, 21)
        
        # Parse calibration coefficients (little-endian format)
        self._calibration = {
            'T1': (calib[0] << 8) | calib[1],
            'T2': (calib[2] << 8) | calib[3],
            'T3': calib[4],
            'P1': (calib[5] << 8) | calib[6] - 2**16,
            'P2': (calib[7] << 8) | calib[6] - 2**16,
            'P3': calib[8],
            'P4': calib[9],
            'P5': (calib[10] << 4) | (calib[11] & 0x0F),
            'P6': (calib[12] << 4) | (calib[11] >> 4),
            'P7': self._twos_complement(calib[13], 8),
            'P8': self._twos_complement(calib[14], 8),
            'P9': self._twos_complement((calib[15] << 8) | calib[16], 16),
            'P10': calib[17],
            'P11': calib[18],
        }

    def _configure_sensor(self):
        """Configure measurement settings"""
        # Set pressure and temperature oversampling + normal mode
        config = 0x33  # 8x oversampling for both, normal mode
        self._i2c.write_bytes(self._REG_CTRL_MEAS, bytes([config]))
        sleep_ms(10)

    def _read_implementation(self):
        """Perform a measurement and return compensated values"""
        # Trigger measurement
        self._i2c.write_bytes(self._REG_CTRL_MEAS, bytes([0x33]))
        
        # Wait for data ready
        while not (self._read_register(self._REG_STATUS, 1)[0] & 0x80):
            sleep_ms(5)

        # Read raw data (3 bytes pressure, 3 bytes temperature)
        data = self._read_register(self._REG_DATA, 6)
        
        raw_press = (data[2] << 16) | (data[1] << 8) | data[0]
        raw_temp = (data[5] << 16) | (data[4] << 8) | data[3]

        return {
            'pressure': self._compensate_pressure(raw_press),
            'temperature': self._compensate_temperature(raw_temp)
        }

    def _compensate_temperature(self, raw_temp):
        """Convert raw temperature to °C using calibration data"""
        # Simplified compensation algorithm
        pd1 = raw_temp - self._calibration['T1']
        pd2 = pd1 * self._calibration['T2']
        return (pd2 + (pd1 ** 2) * self._calibration['T3']) / 100

    def _compensate_pressure(self, raw_press):
        """Convert raw pressure to hPa using calibration data"""
        # Simplified compensation algorithm
        pd1 = self._calibration['P6'] * raw_press
        pd2 = self._calibration['P7'] * raw_press ** 2
        pd3 = self._calibration['P8'] * raw_press ** 3
        return (raw_press + (pd1 + pd2 + pd3) / 100) / 100

    @staticmethod
    def _twos_complement(value, bits):
        """Convert unsigned to signed integer"""
        if value >= (1 << (bits - 1)):
            value -= 1 << bits
        return value

