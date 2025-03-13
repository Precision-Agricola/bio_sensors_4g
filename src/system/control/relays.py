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
    """
    Control class for sensor power relays.
    Handles mutually relay pins (multiplexed channel)
    where only one can be active at a time.
    """
    def __init__(self, relay_pin_a=13, relay_pin_b=14):
        """Initialize the sensor relay pins"""
        self.relay_a = Pin(relay_pin_a, Pin.OUT, value=0)
        self.relay_b = Pin(relay_pin_b, Pin.OUT, value=0)
        self.active_relay = None
    
    def activate_a(self):
        """Activate relay A and ensure relay B is deactivated"""
        self.relay_b.on()
        self.relay_a.on()
        self.active_relay = 'A'
    
    def activate_b(self):
        """Activate relay B and ensure relay A is deactivated"""
        self.relay_a.on()
        self.relay_b.on()
        self.active_relay = 'B'
    
    def deactivate_all(self):
        """Turn off both relays"""
        self.relay_a.off()
        self.relay_b.off()
        self.active_relay = None
    
    def get_active(self):
        """Return the currently active relay identifier or None"""
        return self.active_relay


class LoadRelay:
    """
    Control class for load relays (e.g., aerators)
    Manages timed operation of loads
    """
    def __init__(self, relay_pins=(12, 27)):
        """Initialize the load relay pins"""
        self.relays = [Pin(pin, Pin.OUT, value=0) for pin in relay_pins]
    
    def turn_on(self, relay_index=None):
        """
        Turn on specified relay or all relays if index is None
        
        Args:
            relay_index: Index of the relay to turn on (0 or 1), or None for all
        """
        if relay_index is None:
            # Turn on all relays
            for relay in self.relays:
                relay.on()
        elif 0 <= relay_index < len(self.relays):
            # Turn on specific relay
            self.relays[relay_index].on()
    
    def turn_off(self, relay_index=None):
        """
        Turn off specified relay or all relays if index is None
        
        Args:
            relay_index: Index of the relay to turn off (0 or 1), or None for all
        """
        if relay_index is None:
            # Turn off all relays
            for relay in self.relays:
                relay.off()
        elif 0 <= relay_index < len(self.relays):
            # Turn off specific relay
            self.relays[relay_index].off()
    
    def cycle(self, on_time, off_time, cycles=1, watchdog=None):
        """
        Run relays in on/off cycle for specified number of cycles
        
        Args:
            on_time: Time in seconds to keep relays on
            off_time: Time in seconds to keep relays off
            cycles: Number of on/off cycles to run
            watchdog: Optional WDT instance to feed during long cycles
        """
        for _ in range(cycles):
            # Turn on phase
            self.turn_on()
            self._wait_with_watchdog(on_time, watchdog)
            
            # Turn off phase
            self.turn_off()
            self._wait_with_watchdog(off_time, watchdog)
    
    def _wait_with_watchdog(self, seconds, watchdog=None):
        """Wait for specified seconds while feeding watchdog if provided"""
        start = time.time()
        while time.time() - start < seconds:
            time.sleep(1)
            if watchdog:
                watchdog.feed()

    def get_state(self, relay_index=None):
        """
        Get the current state of specified relay or all relays
        
        Args:
            relay_index: Index of the relay to check (0 or 1), or None for all
            
        Returns:
            If relay_index is None: list of states for all relays
            If relay_index is specified: state of that relay (True/False)
        """
        if relay_index is None:
            return [relay.value() == 1 for relay in self.relays]
        elif 0 <= relay_index < len(self.relays):
            return self.relays[relay_index].value() == 1
        return None
