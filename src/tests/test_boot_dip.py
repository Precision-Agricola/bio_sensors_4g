"""Testing the DIP SWITCH to check the modes"""

from machine import Pin
import time

d1 = Pin(25, Pin.IN, Pin.PULL_DOWN)
d2 = Pin(26, Pin.IN, Pin.PULL_DOWN)

while True:
    time.sleep(2)
    print(f"Pin 25 value: {d1.value()}")
    print(f"pin,26 value: {d2.value()}")
