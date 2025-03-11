"""Test the i2c using raw code and bmp library"""

from system.control.relays import SensorRelay
from utils.micropython_bmpxxx import bmpxxx
from machine import SoftI2C, Pin
import time

relay = SensorRelay()
relay.activate_a()
time.sleep(2)

i2c = SoftI2C(scl=Pin(23), sda=Pin(21))

devices = i2c.scan()

if devices:
    print("Dispositivos I2C encontrados:", [hex(d) for d in devices])
else:
    print("No se encontraron dispositivos I2C")

relay.deactivate_all()
