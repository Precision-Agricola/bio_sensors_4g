# /test_remote_updates/download_to_modem.py
import time
from pico_lte.core import PicoLTE
from pico_lte.utils.status import Status

# --- Configuración ---
# ESTA ES UNA URL PÚBLICA REAL Y FUNCIONAL PARA TUS PRUEBAS.
# Contiene un archivo 'client.zip' de ejemplo.
# En un caso real, reemplazarías esta URL por la de tu propio servidor.
DOWNLOAD_URL = "http://64.227.98.125/client.zip"
FILENAME_ON_MODEM = "client.zip"

def manual_http_download(lte, url, filename):
    """
    Función para descargar un archivo vía HTTP usando comandos AT directos.
    """
    print("\n--- Iniciando descarga HTTP manual ---")
    atcom = lte.atcom
    
    # Paso 1: Configurar el ID de contexto para la sesión HTTP (usamos el contexto 1 que activamos)
    print("1. Configurando contexto HTTP...")
    result = atcom.send_at_comm('AT+QHTTPCFG="contextid",1')
    if result['status'] != Status.SUCCESS: return result
    
    # Paso 2: Indicar al módem la longitud de la URL
    url_len = len(url)
    print(f"2. Enviando URL al módem (longitud: {url_len})...")
    result = atcom.send_at_comm(f'AT+QHTTPURL={url_len},80', "CONNECT")
    if result['status'] != Status.SUCCESS: return result
    
    # Paso 3: Enviar la URL en sí, ahora que el módem espera los datos
    result = atcom.send_at_comm(url)
    if result['status'] != Status.SUCCESS: return result
    print(" -> URL aceptada por el módem.")

    # Paso 4: Ejecutar el comando GET
    print("3. Ejecutando petición HTTP GET...")
    result = atcom.send_at_comm('AT+QHTTPGET=80', desired="+QHTTPGET: 0,200", timeout=85)
    if result['status'] != Status.SUCCESS:
        print("   -> Error en la petición GET o código de respuesta no fue 200 OK.")
        return result
    print("   -> Petición GET exitosa (HTTP 200 OK). Datos recibidos en buffer del módem.")

    # Paso 5: Guardar los datos del buffer en un archivo en UFS
    print(f"4. Guardando datos en el archivo '{filename}'...")
    result = atcom.send_at_comm(f'AT+QHTTPREADFILE="{filename}",80', "OK", timeout=85)
    if result['status'] != Status.SUCCESS:
        print("   -> Error al guardar el archivo en el módem.")
        return result

    print("   -> Archivo guardado correctamente en el módem.")
    return {"status": Status.SUCCESS, "response": f"Archivo '{filename}' descargado."}


# --- Script Principal ---
print("--- Script para Descargar Archivo al Módem vía Celular (v3 - URL Real) ---")
lte_instance = None
try:
    lte_instance = PicoLTE()
    
    print("\nPaso A: Registrando en la red celular...")
    result = lte_instance.network.register_network() 
    if result["status"] != Status.SUCCESS:
        raise Exception("No se pudo registrar en la red celular.")
    print(" -> Registrado en la red celular.")
    
    print("\nPaso B: Activando contexto de datos (PDP)...")
    result = lte_instance.network.get_pdp_ready()
    if result["status"] != Status.SUCCESS:
        raise Exception("No se pudo activar el contexto de datos (PDP).")
    print(" -> Contexto de datos activo. ¡Ya hay internet!")
    
    result = manual_http_download(lte_instance, DOWNLOAD_URL, FILENAME_ON_MODEM)
    
    if result["status"] == Status.SUCCESS:
        print(f"\n¡Descarga completada con éxito!")
        print(f"Respuesta final: {result.get('response')}")
    else:
        print("\nError durante la descarga HTTP.")
        print(f"Respuesta del módem: {result.get('response')}")

except Exception as e:
    print(f"\n[ERROR FATAL] {e}")

finally:
    if lte_instance:
        print("\nDesactivando contexto de datos...")
        lte_instance.network.deactivate_pdp_context()
        print(" -> Contexto de datos desactivado.")

print("\n--- Fin del script ---")