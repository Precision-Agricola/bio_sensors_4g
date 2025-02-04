"""I2C Temperature sensor: SCD41

Prototype code, the final temperature sensor is not this model - SCD41 nor DTH22
"""
from ..base import SensorBase
from machine import I2C, Pin
import time

class SCD41(SensorBase):
    """SCD41 CO2, Temperature and Humidity sensor"""

    I2C_ADDRESS = 0x62

    def __init__(self, i2c, name="SCD41"):
        super().__init__(name)
        self.i2c = i2c
        self.address = self.I2C_ADDRESS

    def initialize(self):
        """Initialize the SCD41 sensor"""
        try:
            # Check if device is present on I2C bus
            if self.address not in self.i2c.scan():
                print(f"SCD41 not found on I2C bus")
                self.connected = False
                return False

            # Stop periodic measurement
            self.i2c.writeto(self.address, b'\x36\x82')
            time.sleep_ms(500)

            self.connected = True
            return True
        except Exception as e:
            print(f"Failed to initialize {self.name}: {str(e)}")
            self.connected = False
            return False

    def read(self):
        """Read CO2, temperature and humidity from SCD41"""
        if not self.connected:
            return None
            
        try:
            # Start measurement
            self.i2c.writeto(self.address, b'\x21\xb1')

            # Wait for measurement (5 seconds according to datasheet)
            time.sleep(5)

            # Read data (9 bytes)
            self.i2c.writeto(self.address, b'\xec\x05')
            data = self.i2c.readfrom(self.address, 9)

            co2 = (data[0] << 8) | data[1]
            temp = -45 + 175 * ((data[3] << 8) | data[4]) / 65535
            hum = 100 * ((data[6] << 8) | data[7]) / 65535

            return {
                "co2": co2,
                "temperature": round(temp, 1),
                "humidity": round(hum, 1)
            }

        except Exception as e:
            print(f"Error reading {self.name}: {str(e)}")
            return None
