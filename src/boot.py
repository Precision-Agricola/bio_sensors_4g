from machine import Pin, WDT
import uos, esp, time
import config.runtime as config

DIP_SW1 = Pin(config.BOOT_SELECTOR_PIN, Pin.IN, Pin.PULL_DOWN)
DIP_SW2 = Pin(config.TEST_SELECTOR_PIN, Pin.IN, Pin.PULL_DOWN)
EMG_RELAYS = (Pin(config.AERATOR_PIN_A, Pin.OUT), Pin(config.AERATOR_PIN_B, Pin.OUT))
DEMO_TIME_FACTOR = 60

print(f"""
       **
      *****
    *********
   ************
  **************    (((((((((#
  ***********   (((((((((((###
 **********  (((((((((((######
 ********   ((((((((((#######
  ******  ((((((((((#######
   *****  (((((((##########
    ***  ((((((##########
      *  ((((##########
         (########
""")

def set_system_mode(mode, time_factor=1):
    config.set_mode(mode)
    config.set_speed(time_factor)
    print(f"""
╔═══════════════════════════════════════════════╗
║        PRECISIÓN AGRÍCOLA - BIO-IOT v1.2      ║
╠═══════════════════════════════════════════════╣
║ Mode: {mode:<18} Time Factor: {time_factor:>3}x    ║
║ SW1: {DIP_SW1.value()} | SW2: {DIP_SW2.value()}                                ║
╚═══════════════════════════════════════════════╝
""")

def emergency_procedure(time_factor=1):
    wdt = WDT(timeout=8000)
    cycle_time = 3 * 3600 // time_factor
    
    while True:
        for r in EMG_RELAYS:
            r.on()
        countdown(cycle_time, wdt)
        
        for r in EMG_RELAYS:
            r.off()
        countdown(cycle_time, wdt)

def countdown(seconds, wdt=None):
    start = time.time()
    while time.time() - start < seconds:
        time.sleep(1)
        if wdt:
            wdt.feed()

dip1, dip2 = DIP_SW1.value(), DIP_SW2.value()

if dip1 and dip2:
    set_system_mode("EMERGENCY MODE")
    emergency_procedure()
elif dip1 and not dip2:
    set_system_mode("WORKING MODE")
    uos.dupterm(None, 0)
    esp.osdebug(None)
elif not dip1 and dip2:
    set_system_mode("DEMO MODE", DEMO_TIME_FACTOR)
    print("Running in accelerated time mode")
elif not dip1 and not dip2:
    set_system_mode("PROGRAM MODE")
    print("Development interfaces active")
else:
    set_system_mode("UNKNOWN MODE")
    print("Error: Invalid switch configuration")
