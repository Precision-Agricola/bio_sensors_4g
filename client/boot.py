from machine import Pin, WDT
import uos
import esp
import time
import gc
import config.runtime as config

print("""
      **
     *****
   *********
  ************
 ************** (((((((((#
 *********** (((((((((((###
 ********** (((((((((((######
 ******** (((((((((#######
  ****** (((((((((########*
   ***** (((((((##########
    *** ((((((##########
     * ((((##########
        (########
""")

print("      Precision Agricola Bioreactores IoT V1.4 - estable")
print("-" * 50)

DIP_SW1 = Pin(config.BOOT_SELECTOR_PIN, Pin.IN, Pin.PULL_DOWN)
DIP_SW2 = Pin(config.TEST_SELECTOR_PIN, Pin.IN, Pin.PULL_DOWN)
EMG_RELAYS = (Pin(config.AERATOR_PIN_A, Pin.OUT), Pin(config.AERATOR_PIN_B, Pin.OUT))

DEMO_TIME_FACTOR = 60

def set_system_mode(mode, time_factor=1):
    config.set_mode(mode)
    config.set_speed(time_factor)
    print(f" Modo Sistema      : {mode:<18}")
    if time_factor != 1:
        print(f" Factor Tiempo     : {time_factor:>3}")
    print(f" Estado Switches   : SW1={DIP_SW1.value()}, SW2={DIP_SW2.value()}")
    print("-" * 40)

def emergency_procedure(time_factor=1):
    print("!!! INICIANDO PROCEDIMIENTO DE EMERGENCIA !!!")
    wdt = WDT(timeout=8000)
    cycle_time = 3 * 3600 // time_factor
    while True:
        print(f"EMG: Encendiendo relés por {cycle_time}s...")
        for r in EMG_RELAYS: r.on()
        _countdown_wdt(cycle_time, wdt)

        print(f"EMG: Apagando relés por {cycle_time}s...")
        for r in EMG_RELAYS: r.off()
        _countdown_wdt(cycle_time, wdt)

def _countdown_wdt(seconds, wdt):
    t0 = time.time()
    while time.time() - t0 < seconds:
        wdt.feed()
        time.sleep(1)

print("Iniciando secuencia de arranque...")

dip1, dip2 = DIP_SW1.value(), DIP_SW2.value()

if dip1 and dip2:
    set_system_mode("EMERGENCY_MODE")
    emergency_procedure()
elif dip1:
    set_system_mode("WORKING_MODE")
    uos.dupterm(None, 0)
    esp.osdebug(None)
elif dip2:
    set_system_mode("DEMO_MODE", DEMO_TIME_FACTOR)
    print(f"Modo DEMO activo (Factor de tiempo: x{DEMO_TIME_FACTOR})")
else:
    set_system_mode("PROGRAM_MODE")
    print("Modo PROGRAM activo (Interfaces de desarrollo activas)")

gc.collect()
print("-" * 60)
print(f"boot.py finalizado. Memoria libre: {gc.mem_free()} bytes.")
