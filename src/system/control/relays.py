from machine import Pin
import time

class SensorRelay:
    def __init__(self, relay_pin_a=13, relay_pin_b=14):
        self.relay_a = Pin(relay_pin_a, Pin.OUT, value=0)
        self.relay_b = Pin(relay_pin_b, Pin.OUT, value=0)
        self.active_relay = None
    
    def activate_a(self):
        self.relay_b.on()
        self.relay_a.on()
        self.active_relay = 'A'
    
    def activate_b(self):
        self.relay_a.on()
        self.relay_b.on()
        self.active_relay = 'B'
    
    def deactivate_all(self):
        self.relay_a.off()
        self.relay_b.off()
        self.active_relay = None
    
    def get_active(self):
        return self.active_relay


class LoadRelay:
    def __init__(self, relay_pins=(0, 27)):
        """Initialize the load relay pins"""
        self.relays = [Pin(pin, Pin.OUT, value=0) for pin in relay_pins]
    
    def turn_on(self, relay_index=None):
        if relay_index is None:
            # Turn on all relays
            for relay in self.relays:
                relay.on()
        elif 0 <= relay_index < len(self.relays):
            # Turn on specific relay
            self.relays[relay_index].on()
    
    def turn_off(self, relay_index=None):
        if relay_index is None:
            # Turn off all relays
            for relay in self.relays:
                relay.off()
        elif 0 <= relay_index < len(self.relays):
            # Turn off specific relay
            self.relays[relay_index].off()
    
    def cycle(self, on_time, off_time, cycles=1, watchdog=None):
       for _ in range(cycles):
            # Turn on phase
            self.turn_on()
            self._wait_with_watchdog(on_time, watchdog)
            
            # Turn off phase
            self.turn_off()
            self._wait_with_watchdog(off_time, watchdog)
    
    def _wait_with_watchdog(self, seconds, watchdog=None):
        start = time.time()
        while time.time() - start < seconds:
            time.sleep(1)
            if watchdog:
                watchdog.feed()

    def get_state(self, relay_index=None):
        if relay_index is None:
            return [relay.value() == 1 for relay in self.relays]
        elif 0 <= relay_index < len(self.relays):
            return self.relays[relay_index].value() == 1
        return None

