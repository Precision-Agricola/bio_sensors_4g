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
    Descarga un archivo de una URL directamente al Pico. Usa el tamaño total 
    obtenido del GET para asegurar una lectura completa y paciente.
    """
    debug.info("\n--- FASE 1: Descarga Directa al Pico (Modo Inteligente) ---")
    
    def _read_line(timeout_ms=5000):
        line_buffer = b''
        start_time = time.ticks_ms()
        while time.ticks_diff(time.ticks_ms(), start_time) < timeout_ms:
            char_byte = picoLTE.atcom.modem_com.read(1)
            if char_byte:
                line_buffer += char_byte
                if char_byte == b'\n': break
        return line_buffer.decode('utf-8', 'ignore').strip()

    # 1. Configurar URL y enviar el comando GET para obtener el tamaño.
    picoLTE.http.set_server_url(url)
    picoLTE.atcom.send_at_comm_once("AT+QHTTPGET=120") # Timeout de 120 segundos
    debug.info("[+] Comando GET enviado. Esperando confirmación y tamaño del módem...")

    total_size = 0
    start_time = time.ticks_ms()
    while time.ticks_diff(time.ticks_ms(), start_time) < 20000: # 20s para obtener respuesta
        line = _read_line()
        if "+QHTTPGET: 0,200" in line:
            debug.info(f"[+] Respuesta HTTP GET recibida: {line}")
            try:
                parts = line.split(',')
                if len(parts) == 3:
                    total_size = int(parts[2])
                    debug.info(f"[+] Éxito: Tamaño del contenido a descargar: {total_size} bytes.")
                    break
            except (ValueError, IndexError): pass
    
    if total_size == 0:
        raise Exception("Fallo al obtener el tamaño de la descarga desde la respuesta +QHTTPGET.")

    # 2. Iniciar la lectura del buffer y esperar el único CONNECT.
    picoLTE.atcom.send_at_comm_once(f"AT+QHTTPREAD={120}") # Timeout de 120 segundos
    
    line = _read_line(timeout_ms=10000)
    while "CONNECT" not in line:
        line = _read_line()
        if not line: raise Exception("No se recibió CONNECT para AT+QHTTPREAD.")
    debug.info("[+] CONNECT recibido. Iniciando lectura de stream binario...")

    # 3. --- BUCLE DE LECTURA "INTELIGENTE" ---
    bytes_read = 0
    try:
        with open(pico_filename, "wb") as f:
            debug.info(f"[+] Iniciando transferencia de datos al archivo '{pico_filename}'...")
            
            # El bucle AHORA SABE CUÁNDO TERMINAR.
            while bytes_read < total_size:
                # Intentamos leer un trozo.
                chunk = picoLTE.atcom.modem_com.read(min(1024, total_size - bytes_read))
                
                if chunk:
                    f.write(chunk)
                    bytes_read += len(chunk)
                    print(f"\r    [INFO] Recibidos {bytes_read} / {total_size} bytes...", end="")
                else:
                    # Si no hay datos, simplemente esperamos un poco y el bucle
                    # volverá a intentarlo, porque bytes_read aún es menor que total_size.
                    time.sleep_ms(20)

            print()

        # 4. Verificación final.
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
        # Limpiar el buffer y detener la sesión HTTP.
        time.sleep(0.5)
        picoLTE.atcom.modem_com.read() # Lee y descarta cualquier dato sobrante
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
