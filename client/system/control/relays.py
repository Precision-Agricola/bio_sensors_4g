from machine import Pin
import time

class SensorRelay:
    def __init__(self, pin_a=13, pin_b=14):
        self.a = Pin(pin_a, Pin.OUT, value=0)
        self.b = Pin(pin_b, Pin.OUT, value=0)
        self.active = None

    def activate_a(self):
        self.a.on()
        self.b.on()
        self.active = 'A'

    def activate_b(self):
        self.a.on()
        self.b.on()
        self.active = 'B'

    def deactivate_all(self):
        self.a.off()
        self.b.off()
        self.active = None

    def get_active(self):
        return self.active


class LoadRelay:
    def __init__(self, pins=(33, 27)): #TODO: chang the solid rele to 33 and perform tests
        self.relays = [Pin(p, Pin.OUT, value=0) for p in pins]

    def turn_on(self, idx=None):
        targets = self.relays if idx is None else [self.relays[idx]]
        for r in targets: r.on()

    def turn_off(self, idx=None):
        targets = self.relays if idx is None else [self.relays[idx]]
        for r in targets: r.off()

    def cycle(self, on_t, off_t, n=1, wdt=None):
        for _ in range(n):
            self.turn_on()
            self._wait(on_t, wdt)
            self.turn_off()
            self._wait(off_t, wdt)

    def _wait(self, secs, wdt=None):
        t0 = time.time()
        while time.time() - t0 < secs:
            time.sleep(1)
            if wdt: wdt.feed()

    def get_state(self, idx=None):
        if idx is None:
            return [r.value() == 1 for r in self.relays]
        return self.relays[idx].value() == 1 if 0 <= idx < len(self.relays) else None
