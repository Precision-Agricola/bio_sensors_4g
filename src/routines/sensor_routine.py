# src/routines/sensor_routine.py
from readings.scheduler import SensorScheduler
from local_network.http_client import HTTPClient 
from local_network.wifi import connect_wifi, verify_wifi_connection, reset_wifi
import ujson as json
import gc
import os
import time

class SensorRoutine:
    def __init__(self, data_folder="data"):
        self.scheduler = SensorScheduler(settling_time=15)
        self.data_folder = data_folder
        self.http_client = HTTPClient()
        
        try:
            os.mkdir(data_folder)
        except OSError:
            pass
        
        self.scheduler.add_callback(self._save_data_callback)
        reset_wifi()
 
    def start(self):
        print("Iniciando rutina de lecturas de sensores...")
        success = self.scheduler.start()
        return success
    
    def stop(self):
        print("Deteniendo rutina de lecturas de sensores...")
        return self.scheduler.stop()
    
    def read_now(self):
        print("Realizando lectura inmediata de sensores...")
        return self.scheduler.read_now()
    
    def _save_data_callback(self, readings):
        if not readings or 'data' not in readings:
            print("No hay datos para guardar")
            return
            
        gc.collect()
            
        try:
            timestamp = readings['timestamp']
            filename = f"{self.data_folder}/sensors_{int(timestamp)}.json"
            
            with open(filename, 'w') as f:
                json.dump(readings, f)
            
            print(f"Datos guardados en {filename}")
            
            # Verificar conexión WiFi antes de intentar enviar
            if not verify_wifi_connection():
                print("Verificación de WiFi fallida, intentando reset...")
                if not reset_wifi():
                    print("Reset de WiFi fallido, guardando en backup...")
                    try:
                        from local_network.wifi import save_to_backup
                        save_to_backup(json.dumps(readings))
                    except Exception as backup_error:
                        print(f"Error al guardar backup: {backup_error}")
                    return
            
            # Continuar con los reintentos de envío HTTP
            retry_count = 0
            max_retries = 3
            while retry_count < max_retries:
                try:
                    print(f"Intento de envío HTTP {retry_count+1}/{max_retries}...")
                    if self.http_client.send_data(readings):
                        print("Datos enviados por HTTP correctamente")
                        break
                    else:
                        print(f"Error al enviar datos por HTTP (intento {retry_count+1})")
                        # Si falla el envío, verificar WiFi nuevamente antes del siguiente intento
                        if retry_count < max_retries - 1 and not verify_wifi_connection():
                            reset_wifi()
                except Exception as e:
                    print(f"Error HTTP: {e}")
                    
                retry_count += 1
                if retry_count < max_retries:
                    time.sleep(2)
                    gc.collect()
            
            gc.collect()
            
        except Exception as e:
            print(f"Error al guardar datos: {e}")
            try:
                from local_network.wifi import save_to_backup
                save_to_backup(json.dumps(readings))
            except:
                pass 

    def check_commands(self):
        """
        Check for commands from the server
        This can be expanded in the future to poll HTTP endpoints for commands
        """
        try:
            if not verify_wifi_connection():
                print("Conexión WiFi no disponible para verificar comandos")
                reset_wifi()  # Intentar resetear WiFi
                return False
            return False  # Por ahora retorna False, pero puedes modificarlo según necesites
        except Exception as e:
            print(f"Error checking commands: {e}")
            return False