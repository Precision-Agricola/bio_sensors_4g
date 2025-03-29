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
        # Import required modules
        from routines.sensor_routine import SensorRoutine
        from utils.connection_manager import ConnectionManager
        from local_network.wifi import connect_wifi
        
        if not connect_wifi():
            print("WiFi not connected. Exiting...")
            return
        
        # Start sensor routine (runs in its own thread)
        sensor_routine = SensorRoutine()
        sensor_routine.start()
        
        # Start aerator cycle in a separate thread (non-blocking)
        import _thread
        _thread.start_new_thread(turn_on_aerators, ())
        
        # Define an async function to run the connection manager heartbeat
        async def demo_mode_async():
            conn_manager = ConnectionManager(uri="ws://192.168.4.1/ws")
            
            async def connection_heartbeat():
                while True:
                    if not conn_manager.connected:
                        print("Heartbeat: Attempting connection...")
                        await conn_manager.connect()
                    else:
                        try:
                            await conn_manager.send("PING")
                        except Exception as e:
                            print("Heartbeat error:", e)
                    await asyncio.sleep(30)  # Check every 30 seconds
            
            # Run the connection manager's run loop and heartbeat concurrently
            asyncio.create_task(conn_manager.run())
            asyncio.create_task(connection_heartbeat())
            # Keep the asyncio loop alive
            while True:
                await asyncio.sleep(3600)
        
        asyncio.run(demo_mode_async())
        
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

