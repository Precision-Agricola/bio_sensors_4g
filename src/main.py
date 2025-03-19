"""
Sensor reading and data transmission code
Precisión Agrícola
Investigation and Development Department
@authors: Caleb De La Vara, Raúl Venegas, Eduardo Santos 
Feb 2025
Modified: March 2025 - Sistema de timer unificado
"""
# src/main.py
import time
from routines.aerator_3hr import turn_on_aerators
import config.runtime as config

def main():
    mode = config.get_mode()
    time_factor = config.get_speed()
    print(f"BIO-IOT v1.2 - Mode: {mode}")
    
   
    if mode == "PROGRAM MODE":
        print("Program mode active - Development interfaces enabled")
        print("No automatic routines will start")
        print("Use REPL to manually control system")
           
    elif mode == "DEMO MODE":
        from routines.sensor_routine import SensorRoutine
        sensor_routine = SensorRoutine()
        sensor_routine.start()
        print(f"Demo mode active - Time acceleration: {time_factor}x")
        print(f"3 hour cycles compressed to {3*60:.1f} minutes")
        turn_on_aerators()
        while True:
            # We're still checking for commands, even though the method currently just returns False
            sensor_routine.check_commands()
            time.sleep(1)
            
    elif mode == "WORKING MODE":
        from routines.sensor_routine import SensorRoutine
        sensor_routine = SensorRoutine()
        sensor_routine.start()

        print("Working mode active - Starting normal operation")
        turn_on_aerators()
        while True:
            sensor_routine.check_commands()
            time.sleep(5)
    else:
        print(f"Mode '{mode}' - Starting basic operation")
        while True:
            sensor_routine.check_commands()
            time.sleep(10)

if __name__ == "__main__":
    main()
    