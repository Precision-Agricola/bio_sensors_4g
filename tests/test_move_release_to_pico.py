# TODO: check the file transfer from the modem to the pico w (currently the file seems to be incomplete)

import time
import os
from pico_lte.utils.status import Status
from pico_lte.core import PicoLTE
from pico_lte.common import debug

# --- Configuración ---
DIRECT_DOWNLOAD_URL = "https://codeload.github.com/Precision-Agricola/bio_sensors_4g/zip/refs/tags/v1.4"
MODEM_FILENAME = "firmware.zip" 
MODEM_FILENAME_WITH_PREFIX = "UFS:" + MODEM_FILENAME
PICO_FILENAME = "firmware_local.zip"

def transfer_modem_to_pico(picoLTE, modem_filename, pico_filename, file_size):
    """
    Transfiere un archivo desde el UFS del módem al sistema de archivos local de la Pico W.
    """
    debug.info(f"\n--- FASE 3: Transfiriendo '{modem_filename}' a la Pico W ---")

    # Helper function para leer una línea directamente del objeto UART.
    def _read_line(timeout_ms=2000):
        """Lee byte a byte desde 'picoLTE.atcom.modem_com'."""
        line_buffer = b''
        start_time = time.ticks_ms()
        while time.ticks_diff(time.ticks_ms(), start_time) < timeout_ms:
            # Usamos el método .read() del objeto UART directamente
            char_byte = picoLTE.atcom.modem_com.read(1)
            if char_byte:
                line_buffer += char_byte
                if char_byte == b'\n':
                    break
        return line_buffer.decode('utf-8', 'ignore').strip()

    # El comando AT+QFDWL se usa para descargar un archivo.
    download_command = f'AT+QFDWL="{modem_filename}"'
    debug.info(f"[+] Enviando comando: {download_command}")

    # Este método es correcto para enviar el comando sin esperar respuesta.
    picoLTE.atcom.send_at_comm_once(download_command)

    # Buscamos la respuesta CONNECT usando nuestro helper
    connect_found = False
    # La respuesta puede tardar un poco, damos un margen.
    for _ in range(10): 
        line = _read_line()
        if line: # Si se leyó algo
            debug.info(f"    ...recibido: {line}")
        if "CONNECT" in line:
            connect_found = True
            break
        if "ERROR" in line or "+CME ERROR" in line:
            debug.error(f"[!] Módem retornó un error: {line}")
            return False

    if not connect_found:
        debug.error("[!] No se recibió 'CONNECT' del módem.")
        return False

    debug.info("[+] Módem en modo de datos. Recibiendo archivo...")

    bytes_read = 0
    try:
        with open(pico_filename, 'wb') as f:
            while bytes_read < file_size:
                # Leemos directamente del objeto UART
                chunk = picoLTE.atcom.modem_com.read(min(1024, file_size - bytes_read))
                if not chunk:
                    debug.warning("\n[!] Timeout durante la lectura del stream de datos.")
                    break
                f.write(chunk)
                bytes_read += len(chunk)
                debug.info(f"    Recibidos {bytes_read} / {file_size} bytes...", end='\r')

        debug.info(f"\n[+] Escritura en '{pico_filename}' completada.")

        # Limpiar las respuestas finales (+QFDWL y OK) del buffer
        time.sleep(0.5)
        final_response = picoLTE.atcom.modem_com.read() # Lee todo lo que quede
        if final_response:
            debug.info(f"[+] Respuesta final del módem: {final_response.decode('utf-8', 'ignore').strip()}")

        # Verificación final
        if os.path.exists(pico_filename) and os.stat(pico_filename)[6] == file_size:
            debug.info("[+] Éxito: El tamaño del archivo local coincide con el esperado.")
            return True
        else:
            local_size = os.stat(pico_filename)[6] if os.path.exists(pico_filename) else 0
            debug.error(f"[!] Fallo: El tamaño del archivo local ({local_size}) no coincide con el esperado ({file_size}).")
            return False

    except Exception as e:
        debug.error(f"[!] Ocurrió una excepción durante la transferencia: {e}")
        return False

# ... (El resto de las funciones y el script principal no necesitan cambios) ...

def cleanup_modem_file(picoLTE, modem_filename_with_prefix):
    """
    Borra un archivo del almacenamiento del módem de forma segura.
    """
    debug.info("\n--- FASE de Limpieza: Intentando borrar archivo del Módem ---")
    
    # El comando AT+QFDEL se usa para borrar archivos. 
    delete_command = f'AT+QFDEL="{modem_filename_with_prefix}"'
    delete_result = picoLTE.atcom.send_at_comm(delete_command)
    debug.info(f"    Respuesta del borrado: {delete_result}")
    
    if delete_result.get("status") == Status.SUCCESS:
        debug.info("[+] Éxito: El archivo fue borrado del módem.")
    else:
        # El error 405 (File not found) es aceptable aquí si el archivo no existía. 
        if "405" in "".join(delete_result.get("response", [])):
            debug.warning("[!] El archivo no existía en el módem, no había nada que borrar.")
        else:
            debug.error(f"[!] Fallo al borrar el archivo del módem.")


# --- INICIO DEL SCRIPT ---
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
    # El comando AT+QFLST se usa para listar archivos. 
    list_command = f'AT+QFLST="{MODEM_FILENAME}"'
    list_result = picoLTE.atcom.send_at_comm(list_command)

    file_size = 0
    if list_result.get("status") == Status.SUCCESS and list_result.get("response"):
        try:
            response_line = list_result['response'][0]
            if "QFLST" in response_line:
                parts = response_line.split(',')
                file_size = int(parts[1])
                debug.info(f"[+] Archivo '{MODEM_FILENAME}' encontrado. Tamaño: {file_size} bytes.")
            else:
                 raise Exception(f"La respuesta de AT+QFLST no tuvo el formato esperado: {response_line}")
        except (ValueError, IndexError) as e:
            debug.error(f"Error al parsear la respuesta de AT+QFLST: {e}")
            raise Exception("No se pudo parsear el tamaño del archivo.")
    else:
        raise Exception(f"No se pudo encontrar el archivo en el módem. Respuesta: {list_result}")

    if transfer_modem_to_pico(picoLTE, MODEM_FILENAME, PICO_FILENAME, file_size):
        debug.info(f"\n[+] Transferencia a la Pico completada. El archivo está en '{PICO_FILENAME}'.")
        
        cleanup_modem_file(picoLTE, MODEM_FILENAME_WITH_PREFIX)

        debug.info("\n--- FASE 5: Listo para servir el archivo localmente ---")
        
    else:
        debug.error("[!] La transferencia del módem a la Pico W falló. Revisar logs.")

except Exception as e:
    debug.error(f"[!] Ocurrió una excepción inesperada: {e}")

finally:
    picoLTE.atcom.send_at_comm("AT+QHTTPSTOP")
    debug.info("\n--- PROCESO FINALIZADO ---")
