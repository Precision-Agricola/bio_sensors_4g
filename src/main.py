"""
Sensor reading and data transmission code
Precisión Agrícola
Investigation and Development Department
@authors: Caleb De La Vara, Raúl Venegas, Eduardo Santos 
Feb 2025
Modified: March 2025 - Sistema de timer unificado
"""
import time
from routines.aerator_3hr import turn_on_aerators
import config.runtime as config

def main():
    """Main application entry point"""
    mode = config.get_mode()
    time_factor = config.get_speed()
    print(f"BIO-IOT v1.2 - Mode: {mode}")

    # Mode operation selector
    if mode == "PROGRAM MODE":
        print("Program mode active - Development interfaces enabled")
        print("No automatic routines will start")
        print("Use REPL to manually control system")
        import sys
        sys.exit(0)
    elif mode == "DEMO MODE":
        from tests.hardware_test import run_hardware_tests
        print(f"Demo mode active - Time acceleration: {time_factor}x")
        print(f"3 hour cycles compressed to {3*60:.1f} minutes")
        print(f"Tests should be running here!")
        run_hardware_tests()
        turn_on_aerators()
    elif mode == "WORKING MODE":
        print("Working mode active - Starting normal operation")
        turn_on_aerators()
    else:
        print(f"Mode '{mode}' - Starting basic operation")
        while True:
            time.sleep(10)
    
if __name__ == "__main__":
    main()
