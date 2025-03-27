"""
Sensor reading and data transmission code
Precisión Agrícola
Investigation and Development Department
@authors: Caleb, Raúl, Eduardo
Feb 2025
Modified: March 2025 - Sistema de timer unificado
"""
import time
import uasyncio as asyncio
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
        # Import sensor routine and connection manager
        from routines.sensor_routine import SensorRoutine
        #from utils.connection_manager import ConnectionManager
        from local_network.wifi import connect_wifi

        if not connect_wifi():
            print("WiFi not connected. Exiting...")
            return

        sensor_routine = SensorRoutine()
        sensor_routine.start()

    elif mode == "WORKING MODE":
        from routines.sensor_routine import SensorRoutine
        #from utils.connection_manager import ConnectionManager
        from local_network.wifi import connect_wifi

        sensor_routine = SensorRoutine()
        sensor_routine.start()

        print("Working mode active - Starting normal operation")
        turn_on_aerators()
        while True:
            sensor_routine.check_commands()
            time.sleep(5)
    else:
        from routines.sensor_routine import SensorRoutine
        #from utils.connection_manager import ConnectionManager
        from local_network.wifi import connect_wifi

        print(f"Mode '{mode}' - Starting basic operation")
        while True:
            sensor_routine.check_commands()
            time.sleep(10)

if __name__ == "__main__":
    main()
