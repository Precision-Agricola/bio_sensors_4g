# /test_remote_updates/download_to_modem.py
import time
from pico_lte.core import PicoLTE
from pico_lte.utils.status import Status

# --- Configuración ---
# REEMPLAZA ESTO con la URL directa a tu archivo .zip
DOWNLOAD_URL = "https://github.com/Precision-Agricola/bio_sensors_4g/blob/remote-updates/client.zip" # Ejemplo con una IP, puede ser un dominio
FILENAME_ON_MODEM = "client.zip"

def manual_http_download(lte, url, filename):
    """
    Función para descargar un archivo vía HTTP usando comandos AT directos,
    ya que la librería no provee una función http.download().
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
    # El módem respondió "CONNECT", ahora enviamos la URL y esperamos "OK"
    result = atcom.send_at_comm(url)
    if result['status'] != Status.SUCCESS: return result
    print(" -> URL aceptada por el módem.")

    # Paso 4: Ejecutar el comando GET
    print("3. Ejecutando petición HTTP GET...")
    # Esperamos el URC "+QHTTPGET: <err>,<http_status_code>,<data_len>"
    # El 0 indica que no hay error en la comunicación.
    result = atcom.send_at_comm('AT+QHTTPGET=80', desired="+QHTTPGET: 0,200", timeout=85)
    if result['status'] != Status.SUCCESS:
        print("   -> Error en la petición GET o código de respuesta no fue 200 OK.")
        return result
    print("   -> Petición GET exitosa (HTTP 200 OK). Datos recibidos en buffer del módem.")

    # Paso 5: Leer los datos del buffer del módem y guardarlos en un archivo en UFS
    print(f"4. Guardando datos en el archivo '{filename}'...")
    # Este comando lee el buffer de la respuesta GET y lo guarda en el almacenamiento interno.
    result = atcom.send_at_comm(f'AT+QHTTPREADFILE="{filename}",80', "OK", timeout=85)
    if result['status'] != Status.SUCCESS:
        print("   -> Error al guardar el archivo en el módem.")
        return result

    print("   -> Archivo guardado correctamente en el módem.")
    return {"status": Status.SUCCESS, "response": f"Archivo '{filename}' descargado."}


# --- Script Principal ---
print("--- Script para Descargar Archivo al Módem vía Celular (v2) ---")
lte_instance = None
try:
    lte_instance = PicoLTE()
    
    # El método correcto para conectarse, usando la máquina de estados de la librería.
    print("\nPaso A: Registrando en la red celular...")
    result = lte_instance.network.register_network() 
    if result["status"] != Status.SUCCESS:
        raise Exception("No se pudo registrar en la red celular.")
    print(" -> Registrado en la red celular.")
    
    # El método correcto para activar la sesión de datos.
    print("\nPaso B: Activando contexto de datos (PDP)...")
    result = lte_instance.network.get_pdp_ready()
    if result["status"] != Status.SUCCESS:
        raise Exception("No se pudo activar el contexto de datos (PDP).")
    print(" -> Contexto de datos activo. ¡Ya hay internet!")
    
    # Llamamos a nuestra función de descarga manual.
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
    # Siempre es buena idea desactivar la sesión de datos para ahorrar energía y datos.
    if lte_instance:
        print("\nDesactivando contexto de datos...")
        # El método correcto para "desconectar".
        lte_instance.network.deactivate_pdp_context()
        print(" -> Contexto de datos desactivado.")

print("\n--- Fin del script ---")