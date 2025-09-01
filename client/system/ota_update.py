# client/system/ota_update.py

import uasyncio as asyncio
import network
import urequests
from utils.logger import log_message

PICO_IP = "192.168.4.1"
FIRMWARE_URL = f"http://{PICO_IP}/client.zip"
SAVE_PATH = "client_update.zip"

async def download_and_apply_update(ssid: str, password: str):
    """Se conecta al AP de la Pico, descarga y aplica la actualización."""
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)
    
    log_message(f"OTA Updater: Conectando a '{ssid}'...")
    
    try:
        wlan.connect(ssid, password)
        
        # Esperar la conexión
        max_wait = 20
        while max_wait > 0 and wlan.status() != 3:
            max_wait -= 1
            log_message("OTA Updater: Esperando conexión...")
            await asyncio.sleep(1)

        if not wlan.isconnected():
            raise Exception("Fallo al conectar al AP de la Pico.")
            
        log_message("OTA Updater: ✅ Conectado. Descargando firmware...")
        
        # Descargar el archivo
        response = urequests.get(FIRMWARE_URL, stream=True)
        if response.status_code == 200:
            with open(SAVE_PATH, "wb") as f:
                while True:
                    chunk = response.raw.read(1024)
                    if not chunk: break
                    f.write(chunk)
            log_message(f"OTA Updater: ✅ Firmware guardado en '{SAVE_PATH}'.")
            
            log_message("OTA Updater: Lógica de descompresión y reinicio pendiente.")
            # 1. Descomprimir el ZIP.
            # 2. Reemplazar archivos .py.
            # 3. Reiniciar el dispositivo.
            
        else:
            raise Exception(f"Error HTTP al descargar: {response.status_code}")

    except Exception as e:
        log_message(f"OTA Updater: ❌ ERROR: {e}")
    finally:
        if wlan.isconnected():
            wlan.disconnect()
        wlan.active(False)
        log_message("OTA Updater: Red de actualización desconectada.")
