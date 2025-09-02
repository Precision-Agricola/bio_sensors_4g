# client/system/ota_update.py

import uasyncio as asyncio
import network
import urequests
from utils.logger import log_message

PICO_IP = "192.168.4.1"
FIRMWARE_URL = f"http://{PICO_IP}/client.zip"
SAVE_PATH = "client_update.zip"

async def download_and_apply_update(wlan, ssid: str, password: str):
    """
    Se conecta al AP de la Pico usando el objeto WLAN compartido,
    descarga y aplica la actualización.
    """
    
    
    if not wlan.active():
        wlan.active(True)
    
    log_message(f"OTA Updater: Iniciando conexión a '{ssid}'...")
    
    try:
        max_retries = 5
        connected = False
        for attempt in range(max_retries):
            log_message(f"OTA Updater: Intento de conexión {attempt + 1}/{max_retries}...")
            try:
                wlan.connect(ssid, password)
                
                wait_time = 10
                while wait_time > 0:
                    if wlan.isconnected():
                        connected = True
                        break
                    wait_time -= 1
                    await asyncio.sleep(1)
                
                if connected:
                    break

            except Exception as e:
                log_message(f"OTA Updater: Error en intento {attempt + 1}: {e}")
                await asyncio.sleep(2)
        
        if not wlan.isconnected():
            raise Exception("Fallo al conectar al AP de la Pico después de varios reintentos.")
            
        log_message(f"OTA Updater: ✅ Conectado. IP: {wlan.ifconfig()[0]}")
        log_message(f"OTA Updater: Descargando firmware desde {FIRMWARE_URL}...")
        
        response = urequests.get(FIRMWARE_URL, stream=True)
        if response.status_code == 200:
            with open(SAVE_PATH, "wb") as f:
                while True:
                    chunk = response.raw.read(1024)
                    if not chunk: break
                    f.write(chunk)
            log_message(f"OTA Updater: ✅ Firmware guardado en '{SAVE_PATH}'.")
            
            log_message("OTA Updater: Lógica de descompresión y reinicio pendiente.")
            
        else:
            raise Exception(f"Error HTTP {response.status_code} al descargar.")

    except Exception as e:
        log_message(f"OTA Updater: ❌ ERROR: {e}")
    finally:
        if wlan.isconnected():
            wlan.disconnect()
        wlan.active(False) 
        log_message("OTA Updater: Red de actualización desconectada.")
