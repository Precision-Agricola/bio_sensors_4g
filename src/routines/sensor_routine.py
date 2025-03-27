from readings.scheduler import SensorScheduler
import ujson as json
import gc
import os
from local_network.ws_client import connect_ws

class SensorRoutine:
    def __init__(self, data_folder="data"):
        self.scheduler = SensorScheduler(settling_time=15)
        self.data_folder = data_folder
        
        try:
            os.mkdir(data_folder)
        except OSError:
            pass
        
        self.scheduler.add_callback(self._save_data_callback)
        
    def start(self):
        print("Starting sensor routine...")
        return self.scheduler.start()
    
    def stop(self):
        print("Stopping sensor routine...")
        return self.scheduler.stop()
    
    def read_now(self):
        print("Performing immediate sensor reading...")
        return self.scheduler.read_now()
    
    def _send_via_websocket(self, readings):
        try:
            ws = connect_ws("ws://192.168.4.1/ws")
            payload = json.dumps(readings)
            ws.send(payload)
            ws.close()
            print("Data sent via WebSocket successfully")
            return True
        except Exception as e:
            print("Error sending via WebSocket:", e)
            return False
    
    def _save_data_callback(self, readings):
        if not readings or 'data' not in readings:
            print("No data to save")
            return
            
        try:
            timestamp = readings['timestamp']
            filename = f"{self.data_folder}/sensors_{int(timestamp)}.json"
            with open(filename, 'w') as f:
                json.dump(readings, f)
            print(f"Data saved in {filename}")
            self._send_via_websocket(readings)
            
            gc.collect()
        except Exception as e:
            print(f"Error saving data: {e}")
