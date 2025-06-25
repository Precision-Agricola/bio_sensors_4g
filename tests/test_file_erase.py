import time
import os
from pico_lte.utils.status import Status
from pico_lte.core import PicoLTE
from pico_lte.common import debug

DIRECT_DOWNLOAD_URL = "https://codeload.github.com/Precision-Agricola/bio_sensors_4g/zip/refs/tags/v1.4"
MODEM_FILENAME = "UFS:firmware_v1.4.zip"

def cleanup_modem_file(picoLTE, modem_filename_with_prefix):
    debug.info("\n--- FASE 2: Iniciando Proceso de Limpieza Segura ---")
    
    picoLTE.atcom.send_at_comm("AT+QHTTPSTOP")
    time.sleep(1)

    debug.info("[+] Consultando manejadores de archivo abiertos (AT+QFOPEN?)...")
    open_files_result = picoLTE.atcom.send_at_comm("AT+QFOPEN?")
    debug.info(f"    Respuesta: {open_files_result}")
    
    file_handle = None
    if open_files_result.get("status") == Status.SUCCESS:
        # --- LA CORRECCIÓN ESTÁ AQUÍ ---
        # Extraemos el nombre base del archivo sin el prefijo "UFS:"
        base_filename = modem_filename_with_prefix.split(':')[-1]
        
        for line in open_files_result.get("response", []):
            # Ahora buscamos el nombre base, que sí coincide con la respuesta del módem
            if base_filename in line:
                try:
                    parts = line.split(',')
                    handle_str = parts[1]
                    file_handle = int(handle_str)
                    debug.info(f"[+] Éxito: Se encontró el handle [{file_handle}] para el archivo.")
                    break
                except (ValueError, IndexError):
                    continue
    
    if file_handle is None:
        debug.warning(f"[!] No se encontró un manejador de archivo abierto para '{modem_filename_with_prefix}'.")
    else:
        debug.info(f"[+] Cerrando archivo con handle [{file_handle}] (AT+QFCLOSE)...")
        close_command = f"AT+QFCLOSE={file_handle}"
        close_result = picoLTE.atcom.send_at_comm(close_command)
        debug.info(f"    Respuesta: {close_result}")
        time.sleep(1)

    debug.info(f"[+] Intentando borrado final de '{modem_filename_with_prefix}'...")
    delete_command = f'AT+QFDEL="{modem_filename_with_prefix}"'
    delete_result = picoLTE.atcom.send_at_comm(delete_command)
    debug.info(f"    Respuesta: {delete_result}")
    
    if delete_result.get("status") == Status.SUCCESS:
        debug.info("[+] Éxito Definitivo: El archivo fue borrado del módem.")
    else:
        debug.error(f"[!] Fallo Final al borrar el archivo.")


picoLTE = PicoLTE()

try:
    debug.info("--- INICIO DEL PROCESO DE DESCARGA Y LIMPIEZA ---")
    
    debug.info("\n[+] Estableciendo conexión de red...")
    picoLTE.network.register_network()
    picoLTE.http.set_context_id()
    picoLTE.network.get_pdp_ready()
    debug.info("[+] Conexión de red lista.")

    debug.info("\n--- FASE 1: Descargando Archivo al Módem ---")
    
    debug.info(f"[+] Estableciendo URL del servidor...")
    picoLTE.http.set_server_url(url=DIRECT_DOWNLOAD_URL)
    
    debug.info("[+] Enviando solicitud GET...")
    picoLTE.http.get()
    
    debug.info("[+] Esperando respuesta del servidor...")
    time.sleep(8)
    
    debug.info(f"[+] Guardando respuesta en el archivo del módem: {MODEM_FILENAME}")
    result = picoLTE.http.read_response_to_file(file_path=MODEM_FILENAME)
    debug.info(f"    Resultado de la descarga: {result}")

    if result.get("status") == Status.SUCCESS:
        debug.info("[+] Éxito: Archivo guardado correctamente en el módem.")
        cleanup_modem_file(picoLTE, MODEM_FILENAME)
    else:
        debug.error("[!] Fallo en la descarga del archivo.")
        cleanup_modem_file(picoLTE, MODEM_FILENAME)

except Exception as e:
    debug.error(f"[!] Ocurrió una excepción inesperada: {e}")

finally:
    debug.info("\n--- PROCESO FINALIZADO ---")