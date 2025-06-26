# client/routines/aerator_routine.py

import time
from config.runtime import get_speed, get_cycle_duration
from system.control.aerator_controller import AeratorController

aerator = AeratorController()

def turn_on_aerators(wdt=None):
    speed = max(1, get_speed())
    cycle_hours = get_cycle_duration()
    on_secs = int(cycle_hours * 3600 * 0.5) // speed

    idx = 0
    while True:
        aerator.turn_on(idx=idx)
        _wait(on_secs, wdt)
        idx = 1 - idx

def _wait(secs, wdt=None):
    t0 = time.time()
    while time.time() - t0 < secs:
        time.sleep(1)
        if wdt: wdt.feed()
