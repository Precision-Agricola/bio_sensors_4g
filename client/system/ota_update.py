# client/system/ota_update.py (VERSIÓN FINAL)
import os
import machine
from utils.logger import log_message

UPDATE_FLAG = 'update.flag'
WIFI_CREDS_FILE = 'wifi_creds.tmp'

def prepare_and_reboot(ssid, password):
    """
    Guarda las credenciales de Wi-Fi, crea la bandera de actualización
    y reinicia el dispositivo en modo actualización.
    """
    log_message("OTA: Preparando para la actualización...")

    try:
        with open(WIFI_CREDS_FILE, 'w') as f:
            f.write(f"{ssid}\n{password}")
        log_message("OTA: Credenciales Wi-Fi temporales guardadas.")
    except Exception as e:
        log_message(f"OTA: Error al guardar credenciales: {e}")
        return

    try:
        with open(UPDATE_FLAG, 'w') as f:
            f.write('1')
        log_message("OTA: Bandera de actualización creada.")
    except Exception as e:
        log_message(f"OTA: Error al crear la bandera de actualización: {e}")
        return

    log_message("OTA: Reiniciando en modo actualización...")
    machine.reset()
