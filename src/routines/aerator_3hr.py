"""
Aerator control routine module for BIO-IOT system
Precision Agrícola - Investigation and Development Department
March 2025
"""
from machine import WDT
from system.control.relays import LoadRelay
import config.runtime as config

def turn_on_aerators():
    """
    Initialize and start the aerator cycle routine.
    Aerators will run for 3 hours on, 3 hours off continuously.
    Time is adjusted according to the system speed factor.
    """
    print("Initializing aerator control routine...")
    
    time_factor = config.get_speed()
    aerator_relays = LoadRelay(relay_pins=(config.AERATOR_PIN_A, config.AERATOR_PIN_B))

    on_time = 3 * 3600 // time_factor
    off_time = 3 * 3600 // time_factor
    
    wdt = WDT(timeout=8000)
    
    print(f"Starting aerator cycle: {on_time}s ON, {off_time}s OFF")
    
    try:
        aerator_relays.cycle(on_time, off_time, cycles=999999, watchdog=wdt)
    except Exception as e:
        print(f"Error in aerator routine: {e}")
        aerator_relays.turn_off()
