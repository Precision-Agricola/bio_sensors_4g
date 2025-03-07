from machine import Pin
import time

pin_25 = Pin(25, Pin.IN, Pin.PULL_DOWN)
pin_26 = Pin(26, Pin.IN, Pin.PULL_DOWN)

while True:
    value_25 = pin_25.value()
    value_26 = pin_26.value()

    time.sleep(1)
    print(f"Reading in Pin {pin_25}, Value: {value_25}")
    print(f"Reading in Pin {pin_26}, Value: {value_26}")
    print("-"*10)