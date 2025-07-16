# /test_remote_updates/test_download_to_modem.py

import time
from pico_lte.core import PicoLTE
from pico_lte.utils.status import Status

# --- Configuración ---
# Usamos la URL directa a 'codeload.github.com' que sabemos que funciona.
DOWNLOAD_URL = "https://codeload.github.com/Precision-Agricola/bio_sensors_4g/zip/refs/tags/v1.4"
# Nombre del archivo como se guardará en el módem.
MODEM_FILENAME = "firmware.zip"
# El prefijo "UFS:" es requerido por algunas funciones para especificar el almacenamiento.
MODEM_FILENAME_WITH_PREFIX = "UFS:" + MODEM_FILENAME

# --- Script Principal ---
print(f"--- Prueba de Descarga: '{MODEM_FILENAME}' ---")
lte_instance = None
try:
    lte_instance = PicoLTE()

    # --- FASE 1: Conexión a la Red ---
    print("\n1. Conectando a la red celular...")
    result = lte_instance.network.register_network()
    if result["status"] != Status.SUCCESS:
        raise Exception("Fallo al registrar en la red.")

    result = lte_instance.network.get_pdp_ready()
    if result["status"] != Status.SUCCESS:
        raise Exception("Fallo al activar el contexto de datos (PDP).")
    print(" -> Conexión exitosa. El módem tiene internet.")

    # --- FASE 2: Descarga HTTP ---
    print("\n2. Configurando y ejecutando descarga HTTP...")
    
    # Estos métodos de la librería envían los comandos AT necesarios.
    lte_instance.http.set_context_id()
    lte_instance.http.set_server_url(url=DOWNLOAD_URL)
    lte_instance.http.get() # Ejecuta el GET
    
    # Pequeña pausa para asegurar que el módem procese la petición GET.
    time.sleep(8) 
    
    print(f" -> Petición GET enviada. Guardando respuesta en '{MODEM_FILENAME}'...")
    
    # Aquí se llama a la función que asumimos ya está corregida en tu librería.
    result = lte_instance.http.read_response_to_file(file_path=MODEM_FILENAME_WITH_PREFIX)
    
    if result.get("status") != Status.SUCCESS:
        raise Exception(f"Fallo al guardar el archivo en el módem. Respuesta: {result}")
    
    print("\n¡ÉXITO! El archivo fue descargado y guardado en el módem.")

except Exception as e:
    print(f"\n[ERROR] El script falló: {e}")

finally:
    # --- FASE 3: Limpieza de la Conexión ---
    if lte_instance:
        print("\n3. Cerrando sesión HTTP y desactivando contexto...")
        lte_instance.atcom.send_at_comm("AT+QHTTPSTOP")
        lte_instance.network.deactivate_pdp_context()
        print(" -> Conexión finalizada correctamente.")

print("\n--- Fin de la prueba ---")