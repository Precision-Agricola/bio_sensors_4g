import time
import os
from pico_lte.utils.status import Status
from pico_lte.core import PicoLTE
from pico_lte.common import debug

# --- Configuración ---
DIRECT_DOWNLOAD_URL = "https://codeload.github.com/Precision-Agricola/bio_sensors_4g/zip/refs/tags/v1.4"
PICO_FILENAME = "firmware_local.zip"

def download_direct_to_pico(picoLTE, url, pico_filename):
    """
    Descarga un archivo de una URL directamente al Pico, esperando la confirmación
    del GET antes de iniciar la lectura para asegurar la sincronización.
    """
    debug.info("\n--- FASE 1: Descarga Directa al Pico (Modo Sincronizado) ---")
    
    def _read_line(timeout_ms=5000):
        line_buffer = b''
        start_time = time.ticks_ms()
        while time.ticks_diff(time.ticks_ms(), start_time) < timeout_ms:
            char_byte = picoLTE.atcom.modem_com.read(1)
            if char_byte:
                line_buffer += char_byte
                if char_byte == b'\n': break
        return line_buffer.decode('utf-8', 'ignore').strip()

    # 1. Configurar URL y enviar el comando GET.
    picoLTE.http.set_server_url(url)
    picoLTE.atcom.send_at_comm_once("AT+QHTTPGET=80")
    debug.info("[+] Comando GET enviado. Esperando confirmación de descarga del módem...")

    # 2. --- AJUSTE DE SINCRONIZACIÓN CLAVE ---
    # Esperar la confirmación "+QHTTPGET: 0,200" antes de continuar.
    # Esto nos asegura que el módem ha terminado de descargar los datos a su buffer.
    get_success = False
    start_time = time.ticks_ms()
    # Damos hasta 80 segundos, igual que el timeout del comando GET.
    while time.ticks_diff(time.ticks_ms(), start_time) < 80000:
        line = _read_line()
        if "+QHTTPGET: 0,200" in line:
            debug.info(f"[+] Confirmación de descarga exitosa recibida: {line}")
            get_success = True
            break
        elif "ERROR" in line or "+QHTTPGET: 1" in line:
            debug.error(f"[!] El módem reportó un error durante el GET: {line}")
            raise Exception("El módem falló al ejecutar HTTP GET.")
    
    if not get_success:
        raise Exception("Timeout esperando la confirmación de la descarga (+QHTTPGET).")

    # 3. Ahora que sabemos que los datos están listos, iniciamos la lectura.
    picoLTE.atcom.send_at_comm_once(f"AT+QHTTPREAD={80}")
    
    line = _read_line(timeout_ms=8000)
    while "CONNECT" not in line:
        line = _read_line()
        if not line:
            raise Exception("No se recibió CONNECT para AT+QHTTPREAD después de un GET exitoso.")
    debug.info("[+] CONNECT recibido. Iniciando lectura de stream binario...")

    # 4. Leer el stream de datos hasta que se agote.
    total_bytes_read = 0
    try:
        with open(pico_filename, "wb") as f:
            while True:
                chunk = picoLTE.atcom.modem_com.read(1024) 
                if chunk:
                    f.write(chunk)
                    total_bytes_read += len(chunk)
                    print(f"\r    [INFO] Recibidos {total_bytes_read} bytes...", end="")
                else:
                    print()
                    debug.info("\n[+] Fin del stream de datos detectado.")
                    break
        
        debug.info(f"[+] Éxito total: Archivo '{pico_filename}' descargado. Tamaño final: {total_bytes_read} bytes.")
        
        if total_bytes_read > 100000: # Asumimos que un firmware válido pesa más de 100kB
            return True
        else:
            debug.error(f"[!] Fallo: El archivo descargado ({total_bytes_read} bytes) parece demasiado pequeño.")
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
    
    # Borrar el archivo local si existiera de un intento anterior.
    try:
        os.remove(PICO_FILENAME)
        debug.info(f"[+] Archivo local anterior '{PICO_FILENAME}' borrado.")
    except OSError:
        pass # El archivo no existía, lo cual es normal.

    # Conexión a la red
    picoLTE.network.register_network()
    picoLTE.http.set_context_id()
    picoLTE.network.get_pdp_ready()
    
    # Llamamos a nuestra función de descarga final
    if download_direct_to_pico(picoLTE, DIRECT_DOWNLOAD_URL, PICO_FILENAME):
        debug.info("\n--- PROCESO FINALIZADO CON ÉXITO ---")
        debug.info(f"El firmware está listo en el archivo local: '{PICO_FILENAME}'")
    else:
        debug.error("\n--- EL PROCESO FALLÓ DURANTE LA DESCARGA ---")

except Exception as e:
    import sys
    print("\n--- REPORTE DE EXCEPCIÓN EN FLUJO PRINCIPAL ---")
    sys.print_exception(e)
    debug.error(f"[!] Ocurrió una excepción inesperada en el flujo principal.")

finally:
    debug.info("[+] Finalizando...")
