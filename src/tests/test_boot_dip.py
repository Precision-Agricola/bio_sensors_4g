"""Testing the DIP SWITCH to check the modes

Tacking advantage in the circuits connected into the pins 25-26.
channel A/B DIP: Will connect into and Op Amp no inverter configuration or Current Driver circuit

By changing the last two channels (from left to right).
Setting the pins as a pull down input, values 0 and 1 logic can be present
"""

from machine import Pin
from time import sleep

d1 = Pin(26, Pin.IN, Pin.PULL_DOWN)
d2 = Pin(26, Pin.IN, Pin.PULL_DOWN)

cycles = 10

for cycle in range(cycles):
    sleep(5)
    print(f"Pin 25 value: {d1.value()}")
    print(f"pin,26 value: {d2.value()}")
