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
import config.runtime as config
from routines.aerator_3hr import turn_on_aerators

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
        from local_network.wifi import connect_wifi
        from tests.test_websocket import ws_client

        # Start sensor routine (runs in its own thread)
        sensor_routine = SensorRoutine()
        sensor_routine.start()

        # Start aerator in a separate thread
        import _thread
        _thread.start_new_thread(turn_on_aerators, ())

        # Run the websocket client async task
        asyncio.run(ws_client())
       
        
    elif mode == "WORKING MODE":
        from routines.sensor_routine import SensorRoutine
        from local_network.wifi import connect_wifi
        
        if not connect_wifi():
            print("WiFi not connected. Exiting...")
            return
        
        sensor_routine = SensorRoutine()
        sensor_routine.start()
        
        print("Working mode active - Starting normal operation")
        # Running the aerator cycle (blocking) in WORKING MODE;
        # consider moving to a thread if you add async tasks here later.
        turn_on_aerators()
        while True:
            sensor_routine.check_commands()
            time.sleep(5)
            
    else:
        from routines.sensor_routine import SensorRoutine
        from local_network.wifi import connect_wifi
        
        print(f"Mode '{mode}' - Starting basic operation")
        while True:
            sensor_routine.check_commands()
            time.sleep(10)

if __name__ == "__main__":
    main()

