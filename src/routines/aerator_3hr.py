"""System base routine"""

from machine import WTD, Timer
from system.control import aerator_relays

THREE_HOURS = 3 * 60 * 60 * 1000
SIX_HOURS = 6 * 60 * 60 * 1000 

wdt = WTD(timeout=SIX_HOURS + 500)

timer = Timer(0)

def turn_on_aerators(fixed_time = None):
    [relay.on() for relay in aerator_relays]
    wdt.feed()
    timer.init(period=THREE_HOURS, mode=Timer.ONE_SHOT, callback=turn_off_aerators)

def turn_off_aerators(fixed_time = None):
    [relay.off() for relay in aerator_relays]
    wdt.feed() 
    timer.init(period=THREE_HOURS, mode=Timer.ONE_SHOT, callback=turn_on_aerators)
