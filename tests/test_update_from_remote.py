
# TODO: this is the most promessing codoeutniln now 
import time
import os
from pico_lte.utils.status import Status
from pico_lte.core import PicoLTE
from pico_lte.common import debug

# --- Configuración ---
DIRECT_DOWNLOAD_URL = "https://codeload.github.com/Precision-Agricola/bio_sensors_4g/zip/refs/tags/v1.4"
PICO_FILENAME = "firmware_local.zip" # El único nombre de archivo que necesitamos ahora

def download_direct_to_pico(picoLTE, url, pico_filename):
    """
    Descarga un archivo de una URL directamente al sistema de archivos del Pico,
    bypassing el UFS del módem para evitar truncamiento.
    """
    debug.info("\n--- FASE 1: Descarga Directa al Pico ---")
    
    # Helper para leer una línea del puerto UART
    def _read_line(timeout_ms=3000):
        line_buffer = b''
        start_time = time.ticks_ms()
        while time.ticks_diff(time.ticks_ms(), start_time) < timeout_ms:
            char_byte = picoLTE.atcom.modem_com.read(1)
            if char_byte:
                line_buffer += char_byte
                if char_byte == b'\n': break
        return line_buffer.decode('utf-8', 'ignore').strip()

    # 1. Configurar y ejecutar la petición GET
    picoLTE.http.set_server_url(url)
    picoLTE.atcom.send_at_comm_once("AT+QHTTPGET=80") # 80 segundos de timeout para el GET

    # 2. Cazar la respuesta +QHTTPGET para obtener el tamaño real del archivo
    total_size = 0
    start_time = time.ticks_ms()
    while time.ticks_diff(time.ticks_ms(), start_time) < 15000:
        line = _read_line()
        if "+QHTTPGET" in line:
            debug.info(f"[+] Respuesta HTTP GET recibida: {line}")
            try:
                parts = line.split(',')
                if len(parts) == 3 and parts[0] == "+QHTTPGET: 0":
                    total_size = int(parts[2])
                    debug.info(f"[+] Éxito: Tamaño del contenido a descargar: {total_size} bytes.")
                    break
            except:
                pass # Ignorar líneas malformadas
    
    if total_size == 0:
        raise Exception("Fallo al obtener el tamaño de la descarga desde la respuesta +QHTTPGET.")

    # 3. Leer el contenido en trozos y escribirlo directamente al archivo del Pico
    bytes_read = 0
    try:
        with open(pico_filename, "wb") as f:
            debug.info(f"[+] Iniciando transferencia de datos al archivo '{pico_filename}'...")
            while bytes_read < total_size:
                # Pedimos al módem el siguiente trozo de datos
                picoLTE.atcom.send_at_comm_once(f"AT+QHTTPREAD={80}") # 80s timeout de lectura
                
                # La respuesta vendrá en formato:
                # CONNECT
                # <datos binarios>
                # OK
                # +QHTTPREAD: <err>,<bytes_leidos>
                
                # Esperamos CONNECT
                line = _read_line()
                while "CONNECT" not in line:
                    line = _read_line(timeout_ms=5000) # Timeout más largo para esperar datos
                    if not line: break # Salir si no hay más respuesta
                if "CONNECT" not in line:
                    debug.error("[!] No se recibió CONNECT para AT+QHTTPREAD.")
                    break

                # Leemos el chunk de datos
                chunk_size_to_read = min(1024, total_size - bytes_read)
                chunk = picoLTE.atcom.modem_com.read(chunk_size_to_read)
                
                if chunk:
                    f.write(chunk)
                    bytes_read += len(chunk)
                    print(f"\r    [INFO] Recibidos {bytes_read} / {total_size} bytes...", end="")
                else:
                    debug.warning("\n[!] No se recibieron más datos del módem.")
                    break
            
            print() # Nueva línea final

        # 4. Verificación final
        if bytes_read >= total_size:
            debug.info(f"[+] Éxito total: Archivo '{pico_filename}' descargado y verificado.")
            return True
        else:
            debug.error(f"[!] Fallo en la descarga. Se recibieron {bytes_read} de {total_size} bytes.")
            return False

    except Exception as e:
        import sys
        print("\n--- REPORTE DE EXCEPCIÓN EN DESCARGA DIRECTA ---")
        sys.print_exception(e)
        return False
    finally:
        picoLTE.atcom.send_at_comm("AT+QHTTPSTOP")

# --- INICIO DEL SCRIPT ---
picoLTE = PicoLTE()

try:
    debug.info("--- INICIO DEL PROCESO COMPLETO ---")
    
    # Como ya no usamos el UFS, no necesitamos limpiar el módem.
    # Podemos borrar el archivo local si existiera de un intento anterior.
    try:
        os.remove(PICO_FILENAME)
        debug.info(f"[+] Archivo local anterior '{PICO_FILENAME}' borrado.")
    except OSError:
        pass # El archivo no existía, lo cual es normal.

    # Conexión a la red
    picoLTE.network.register_network()
    picoLTE.http.set_context_id()
    picoLTE.network.get_pdp_ready()
    
    # Llamamos a nuestra nueva y robusta función de descarga
    if download_direct_to_pico(picoLTE, DIRECT_DOWNLOAD_URL, PICO_FILENAME):
        debug.info("\n--- PROCESO FINALIZADO CON ÉXITO ---")
        debug.info(f"El firmware está listo en el archivo local: '{PICO_FILENAME}'")
        # Aquí iría tu lógica para servir el archivo a los ESP32
    else:
        debug.error("\n--- EL PROCESO FALLÓ DURANTE LA DESCARGA ---")

except Exception as e:
    debug.error(f"[!] Ocurrió una excepción inesperada en el flujo principal: {e}")

finally:
    debug.info("[+] Finalizando...")
