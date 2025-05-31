from machine import Pin, SoftI2C
from config.config import I2C_SCL_PIN, I2C_SDA_PIN
import time


time.sleep(1)  # Espera a que el sensor se energice

i2c = SoftI2C(scl=Pin(I2C_SCL_PIN), sda=Pin(I2C_SDA_PIN))
devices = i2c.scan()

print("I2C devices found:" if devices else "No I2C devices found.")
for d in devices:
    print(" - Address: 0x{:02X}".format(d))

relay.deactivate_all()
