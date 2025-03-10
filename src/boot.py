from machine import Pin, WDT
import uos, esp, time

DIP_SW1 = Pin(25, Pin.IN, Pin.PULL_DOWN)
DIP_SW2 = Pin(26, Pin.IN, Pin.PULL_DOWN)
EMG_RELAYS = (Pin(12, Pin.OUT), Pin(27, Pin.OUT))

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

def display_banner(mode, time_factor=1):
    print(f"""
╔═══════════════════════════════════════════════╗
║        PRECISIÓN AGRÍCOLA - BIO-IOT v1.2      ║
╠═══════════════════════════════════════════════╣
║ Mode: {mode:<18} Time Factor: {time_factor:>3}x ║
║ SW1: {DIP_SW1.value()} | SW2: {DIP_SW2.value()}                             ║
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
    display_banner("EMERGENCY MODE")
    emergency_procedure()

elif dip2 and not dip1:
    display_banner("TEST MODE")
    # import tests.hardware_test

elif dip1 and not dip2:  # SW1 UP, SW2 DOWN
    display_banner("DEMO MODE", DEMO_TIME_FACTOR)
    emergency_procedure(DEMO_TIME_FACTOR)
    # Add other demo-accelerated routines here

elif not dip1 and dip2:
    display_banner("WORKING MODE")
    uos.dupterm(None, 0)
    esp.osdebug(None)

else:
    display_banner("PROGRAM MODE")
    print("Development interfaces active")
