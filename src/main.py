"""
Sensor reading and data transmission code
Precisión Agrícola
Investigation and Development Department
@authors: Caleb, Raúl, Eduardo
Feb 2025
Modified: March 2025 - Sistema de timer unificado
"""
import uasyncio as asyncio
import config.runtime as config
from routines.aerator_3hr import turn_on_aerators

def main():
    mode = config.get_mode()
    print(f"BIO-IOT v1.2 - Mode: {mode}")

    if mode == "PROGRAM MODE":
        print("Program mode active - Development interfaces enabled")
        print("No automatic routines will start")
        print("Use REPL to manually control system")
           
    elif mode == "DEMO MODE":
        from routines.sensor_routine import SensorRoutine
        from local_network.websocket_client import websocket_client 
        import _thread
        import uos, esp

        uos.dupterm(None, 0)
        esp.osdebug(None)


        # Start sensor routine (runs in its own thread)
        sensor_routine = SensorRoutine()
        sensor_routine.start()

        # Start aerator in a separate thread
        _thread.start_new_thread(turn_on_aerators, ())

        # Run the websocket client async task - pass the sensor_routine instance
        asyncio.run(websocket_client(sensor_routine))
        
    elif mode == "WORKING MODE":
        import  uos, esp
        from routines.sensor_routine import SensorRoutine
        from local_network.websocket_client import websocket_client

        # Disable REPL and OSDebug
        uos.dupterm(None, 0)
        esp.osdebug(None)

        # Start sensor routine (runs in its own thread)
        sensor_routine = SensorRoutine()
        sensor_routine.start()

        # Start aerator in a separate thread
        import _thread
        _thread.start_new_thread(turn_on_aerators, ())

        # Run the websocket client async task
        asyncio.run(websocket_client())
        
        print(f"Mode '{mode}' - Starting basic operation")

if __name__ == "__main__":
    main()

