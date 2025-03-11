"""
Relay Classes

Relays are mainly two types: 
    a) Load relays (Board pines 12, 27) and,
    b) Sensing bus relays (13, 14).


The sensing relays are mutual opposite in order to enable only one side communication.
There is an RTC circuit connected to shared pines with the dev board and the gas sensors.
Control relays or load relays are connected to the same load in the current version
in order to reduce the wear in it.

Note: The pins are not taking for the config file because they can be modified since the 
dev board is a 3th party hardware.
"""
from machine import Pin
import time

class SensorRelay:
    """Control class for sensors power relays."""

    def __init__(self, relay_pin_a = 13, relay_pin_b = 14):
        """Initialize the sensor relay pins. The pins activation should be exclusive (opposite states)"""
        self.relay_a = Pin(relay_pin_a, Pin.OUT, value=0)
        self.relay_b = Pin(relay_pin_b, Pin.OUT, value=0) 
        self.active_relay = None
    
    def activate_a(self):
        """Activate Channel A relay"""
        self.relay_a.on()
        self.relay_b.off()
        self.active_relay = 'A'
    
    def activate_b(self):
        """Activate Channel B relay"""
        self.relay_a.off()
        self.relay_b.on()
        self.active_relay = 'B'
    

    def deactivate_all(self):
        """Deactivate all channel A and B"""
        self.relay_a.off()
        self.relay_b.off()
        self.active_relay = None
    
    def get_active(self):
        """Show what are t"""
        self.active_relay


class LoadRelay:
    """Control the load relays (Aerator in V1.2)"""
    def __init__(self, relay_pins = (12,27)):
        self.relays = [Pin(pin, Pin.OUT, value = 0) for pin in relay_pins]
    
    def turn_on(self, relay_index = None):
        """Activate a specific relay by index"""
        if relay_index is None:
            for relay in self.relays:
                relay.on()
        elif 0 <= relay_index < len(self.relays):
            self.relays[relay_index].on()
    
    def turn_off(self, relay_index = None):
        if relay_index is None:
            for relay in self.relays:
                relay.off()
        elif 0 <= relay_index < len(self.relays):
            self.relays[relay_index].off()


    def cycle(self, on_time, off_time, cycles = 1, watchdog = None):
        for _ in range(cycles):
            self.turn_on()
            self._wait_with_watchdog(on_time, watchdog)
            self.turn_off()
            self._wait_with_watchdog(on_time, watchdog)
    
    def _wait_with_watchdog(self, seconds, watchdog=None):
        start = time.time()
        while time.time() - start < seconds:
            time.sleep(1)
            if watchdog:
                watchdog.feed()
