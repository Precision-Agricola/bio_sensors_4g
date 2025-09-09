# client/updater.py
import network
import urequests
import os
import tarfile
import machine
import time

# --- Configuración ---
UPDATE_FLAG = 'update.flag'
UPDATE_ARCHIVE = 'update.tar'
SERVER_IP = '192.168.4.1' # IP del AP del servidor
FIRMWARE_URL = f"http://{SERVER_IP}/client.tar" # Asumimos que el server siempre lo sirve con este nombre

def clean_old_firmware():
    """Borra de forma segura los archivos del firmware antiguo."""
    print("Borrando firmware antiguo...")
    for item in FILES_TO_DELETE:
        try:
            # Comprobar si es directorio o archivo para usar el método correcto
            if os.stat(item)[0] & 0x4000: # Es un directorio
                # Borrado recursivo simple
                for file in os.listdir(item):
                    os.remove(item + '/' + file)
                os.rmdir(item)
                print(f"  Directorio borrado: {item}")
            else: # Es un archivo
                os.remove(item)
                print(f"  Archivo borrado: {item}")
        except OSError as e:
            if e.args[0] == 2: # ENOENT: No such file or directory
                print(f"  '{item}' no existía, omitiendo.")
            else:
                raise e

def extract_archive(archive_name):
    """Extrae el contenido de un archivo .tar."""
    print(f"Extrayendo '{archive_name}'...")
    try:
        tar = tarfile.TarFile(archive_name)
        for member in tar:
            if member.type == tarfile.REGTYPE:
                parts = member.name.split('/')
                filename = parts.pop()
                if parts:
                    path = "/".join(parts)
                    current_path = ""
                    for part in path.split('/'):
                        current_path += part
                        try:
                            os.mkdir(current_path)
                        except OSError as e:
                            if e.args[0] != 17: raise
                        current_path += "/"
                print(f"  Extrayendo: {member.name}")
                sub_file = tar.extractfile(member)
                with open(member.name, "wb") as f:
                    f.write(sub_file.read())
        tar.close()
        return True
    except Exception as e:
        print(f"¡¡¡ ERROR FATAL AL EXTRAER: {e} !!!")
        return False

def run():
    """Función principal que se ejecuta en modo actualización."""
    print("--- MODO ACTUALIZACIÓN ---")

    # 1. Conectarse al AP del Servidor
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)

    # Recibe las credenciales guardadas por el uart_listener
    ssid, password = "", ""
    try:
        with open('wifi_creds.tmp', 'r') as f:
            ssid, password = f.read().strip().splitlines()
        os.remove('wifi_creds.tmp')
    except Exception as e:
        print(f"Error leyendo credenciales temporales: {e}")
        # Si falla, limpiamos y reiniciamos para evitar un bucle
        if os.path.exists(UPDATE_FLAG): os.remove(UPDATE_FLAG)
        machine.reset()

    print(f"Conectando a '{ssid}'...")
    wlan.connect(ssid, password)

    max_wait = 15
    while max_wait > 0:
        if wlan.isconnected():
            print(f"Conexión exitosa. IP: {wlan.ifconfig()[0]}")
            break
        max_wait -= 1
        time.sleep(1)

    if not wlan.isconnected():
        print("¡Fallo al conectar con el servidor!")
        # Limpiamos y reiniciamos
        if os.path.exists(UPDATE_FLAG): os.remove(UPDATE_FLAG)
        machine.reset()

    # 2. Descargar el archivo
    print(f"Descargando desde {FIRMWARE_URL}...")
    try:
        response = urequests.get(FIRMWARE_URL)
        if response.status_code == 200:
            with open(UPDATE_ARCHIVE, "wb") as f:
                f.write(response.content)
            print("Descarga completa.")
            response.close()
        else:
            raise Exception(f"Error HTTP {response.status_code}")
    except Exception as e:
        print(f"¡Fallo en la descarga: {e}!")
        # Limpiamos y reiniciamos
        if os.path.exists(UPDATE_FLAG): os.remove(UPDATE_FLAG)
        machine.reset()

    wlan.disconnect()
    wlan.active(False)

    # 3. Aplicar la actualización (lógica de tu prototipo)
    clean_old_firmware()
    if extract_archive(UPDATE_ARCHIVE):
        print("Actualización completada con éxito.")
        os.remove(UPDATE_ARCHIVE)
    else:
        print("¡¡¡ LA ACTUALIZACIÓN FALLÓ !!!")
        # Podríamos reintentar o usar un fallback aquí. Por ahora, reiniciamos.

    # 4. Limpieza final y reinicio a modo normal
    print("Limpiando bandera y reiniciando en modo normal...")
    os.remove(UPDATE_FLAG)
    machine.reset()
