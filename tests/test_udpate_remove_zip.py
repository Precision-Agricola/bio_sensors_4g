import time
import os
from pico_lte.utils.status import Status
from pico_lte.core import PicoLTE
from pico_lte.common import debug

DIRECT_DOWNLOAD_URL = "https://codeload.github.com/Precision-Agricola/bio_sensors_4g/zip/refs/tags/v1.4"
MODEM_FILENAME = "firmware.zip" 
MODEM_FILENAME_WITH_PREFIX = "UFS:" + MODEM_FILENAME
PICO_FILENAME = "firmware_local.zip"

def transfer_modem_to_pico(picoLTE, modem_filename, pico_filename, file_size):
    debug.info(f"\n--- FASE 2: Transfiriendo '{modem_filename}' a la Pico W ---")
    
    download_command = f'AT+QFDWL="{modem_filename}"'
    debug.info(f"[+] Enviando comando: {download_command}")
    picoLTE.atcom.at_port.write(download_command.encode('utf-8') + b'\r\n')
    time.sleep(0.5) 
    response_lines = picoLTE.atcom.at_port.read(256).decode('utf-8', 'ignore')
    if "CONNECT" not in response_lines:
        debug.error(f"[!] No se recibió 'CONNECT' del módem. Respuesta: {response_lines}")
        return False
    debug.info("[+] Módem en modo de datos. Recibiendo archivo...")
    
    bytes_read = 0
    try:
        with open(pico_filename, 'wb') as f:
            while bytes_read < file_size:
                # Ajustar el tamaño del buffer según la memoria disponible en la Pico
                chunk_size = min(1024, file_size - bytes_read)
                chunk = picoLTE.atcom.at_port.read(chunk_size)
                if not chunk:
                    # Timeout o fin de stream inesperado
                    break
                f.write(chunk)
                bytes_read += len(chunk)
                debug.info(f"    Recibidos {bytes_read} / {file_size} bytes...", end='\r')

        debug.info(f"\n[+] Escritura en '{pico_filename}' completada.")

        # Limpiar las respuestas finales (+QFDWL y OK) del buffer del puerto serie
        time.sleep(1)
        final_response = picoLTE.atcom.at_port.read(256).decode('utf-8', 'ignore')
        debug.info(f"[+] Respuesta final del módem: {final_response.strip()}")
        
        if os.stat(pico_filename)[6] == file_size:
            debug.info("[+] Éxito: El tamaño del archivo local coincide con el esperado.")
            return True
        else:
            debug.error(f"[!] Fallo: El tamaño del archivo local ({os.stat(pico_filename)[6]}) no coincide con el esperado ({file_size}).")
            return False

    except Exception as e:
        debug.error(f"[!] Ocurrió una excepción durante la transferencia: {e}")
        return False

def cleanup_modem_file(picoLTE, modem_filename_with_prefix):
    debug.info("\n--- FASE 4: Iniciando Proceso de Limpieza Segura del Módem ---")
    picoLTE.atcom.send_at_comm("AT+QHTTPSTOP")
    time.sleep(1)
    
    debug.info(f"[+] Intentando borrado final de '{modem_filename_with_prefix}'...")
    delete_command = f'AT+QFDEL="{modem_filename_with_prefix}"'
    delete_result = picoLTE.atcom.send_at_comm(delete_command)
    debug.info(f"    Respuesta: {delete_result}")
    
    if delete_result.get("status") == Status.SUCCESS:
        debug.info("[+] Éxito Definitivo: El archivo fue borrado del módem.")
    else:
        debug.error(f"[!] Fallo Final al borrar el archivo del módem.")

picoLTE = PicoLTE()

try:
    debug.info("--- INICIO DEL PROCESO COMPLETO ---")
    
    cleanup_modem_file(picoLTE, MODEM_FILENAME_WITH_PREFIX)

    debug.info("\n--- FASE 1: Descargando Archivo al Módem ---")
    picoLTE.network.register_network()
    picoLTE.http.set_context_id()
    picoLTE.network.get_pdp_ready()
    
    picoLTE.http.set_server_url(url=DIRECT_DOWNLOAD_URL)
    picoLTE.http.get()
    time.sleep(8)
    
    result = picoLTE.http.read_response_to_file(file_path=MODEM_FILENAME_WITH_PREFIX)
    debug.info(f"    Resultado de la descarga al módem: {result}")
    
    if result.get("status") != Status.SUCCESS:
        raise Exception("Fallo en la descarga HTTP al módem.")

    debug.info("[+] Éxito: Archivo guardado correctamente en el módem.")
    picoLTE.atcom.send_at_comm("AT+QHTTPSTOP")
    time.sleep(1)

    debug.info(f"\n--- FASE 2: Verificando archivo en el módem ---")
    list_result = picoLTE.file.list_files(MODEM_FILENAME)
    file_size = 0
    if list_result.get("status") == Status.SUCCESS and list_result.get("response"):
        try:
            parts = list_result['response'][0].split(',')
            file_size = int(parts[1])
            debug.info(f"[+] Archivo '{MODEM_FILENAME}' encontrado en UFS. Tamaño: {file_size} bytes.")
        except (ValueError, IndexError):
            raise Exception("No se pudo parsear el tamaño del archivo desde AT+QFLST.")
    else:
        raise Exception("No se pudo encontrar el archivo en el módem después de la descarga.")

    if transfer_modem_to_pico(picoLTE, MODEM_FILENAME, PICO_FILENAME, file_size):
        debug.info(f"\n[+] Transferencia completada. El archivo está en '{PICO_FILENAME}'.")
        
        cleanup_modem_file(picoLTE, MODEM_FILENAME_WITH_PREFIX)

        debug.info("\n--- FASE 5: Listo para servir el archivo localmente ---")
        
    else:
        debug.error("[!] La transferencia del módem a la Pico W falló. Revisar logs.")

except Exception as e:
    debug.error(f"[!] Ocurrió una excepción inesperada: {e}")

finally:
    debug.info("\n--- PROCESO FINALIZADO ---")