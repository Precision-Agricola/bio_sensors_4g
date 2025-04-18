from system.control.relays import LoadRelay
import config.runtime as runtime_config

def turn_on_aerators():
    print("Initializing aerator control routine...")
    time_factor = runtime_config.get_speed()
    aerator_relays = LoadRelay()

    on_time = 3 * 3600 // time_factor
    off_time = 3 * 3600 // time_factor
    
    print(f"Starting aerator cycle: {on_time}s ON, {off_time}s OFF")
    
    try:
        aerator_relays.cycle(on_time, off_time, cycles=999999)
    except Exception as e:
        print(f"Error in aerator routine: {e}")
        aerator_relays.turn_off()
