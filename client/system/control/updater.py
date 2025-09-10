# client/system/updater.py

import network
import urequests
import os
import tarfile
import machine
import time
import gc

UPDATE_FLAG = 'update.flag'
UPDATE_ARCHIVE = 'update.tar'
WIFI_CREDS_FILE = 'wifi_creds.tmp'
STAGING_DIR = 'update_tmp'
SERVER_IP = '192.168.4.1'
FIRMWARE_URL = f"http://{SERVER_IP}/client.tar"

FILES_TO_DELETE = [
    'main.py', 'calendar', 'config', 'protocols', 'readings',
    'routines', 'sensors', 'tests', 'utils', 'system'
]

def delete_recursive(path):
    """Borra un directorio y todo su contenido de forma recursiva."""
    try:
        for entry in os.ilistdir(path):
            full_path = f"{path}/{entry[0]}"
            if entry[1] == 0x4000:
                delete_recursive(full_path)
            else:
                os.remove(full_path)
        os.rmdir(path)
        print(f"  Directorio borrado: {path}")
    except Exception as e:
        print(f"  Aviso al borrar {path}: {e}")

def clean_old_firmware():
    """Borra los archivos del firmware antiguo listados en FILES_TO_DELETE."""
    print("Borrando firmware antiguo de la raíz...")
    for item in FILES_TO_DELETE:
        try:
            if item in os.listdir('/'):
                if os.stat(item)[0] & 0x4000:
                    delete_recursive(item)
                else:  # Es un archivo
                    os.remove(item)
                    print(f"  Archivo borrado: {item}")
        except Exception as e:
            print(f"  Error borrando {item}: {e}")


def extract_archive_to_staging(archive_name):
    """
    Extrae el .tar a una carpeta temporal, quitando el prefijo 'client/'.
    """
    print(f"Extrayendo '{archive_name}' a la carpeta temporal '{STAGING_DIR}'...")
    try:
        os.mkdir(STAGING_DIR)
        tar = tarfile.TarFile(archive_name)
        for member in tar:
            if member.type == tarfile.REGTYPE:

                target_path = member.name.replace('client/', '', 1)
                parts = target_path.split('/')

                if len(parts) > 1:
                    path_in_staging = f"{STAGING_DIR}/{'/'.join(parts[:-1])}"
                    try:
                        os.makedirs(path_in_staging)
                    except OSError as e:
                        if e.args[0] != 17: raise
                
                sub_file = tar.extractfile(member)
                with open(f"{STAGING_DIR}/{target_path}", "wb") as f:
                    f.write(sub_file.read())

        tar.close()
        os.remove(archive_name)
        print("Extracción a temporal completada.")
        return True
    except Exception as e:
        print(f"¡ERROR FATAL AL EXTRAER A TEMPORAL: {e}!")
        return False

def apply_update_from_staging():
    """Mueve los archivos desde la carpeta temporal a la raíz."""
    print(f"Aplicando actualización desde '{STAGING_DIR}'...")
    try:
        for item in os.listdir(STAGING_DIR):
            source = f"{STAGING_DIR}/{item}"
            destination = f"/{item}"
            os.rename(source, destination)
            print(f"  Movido: {item}")
        delete_recursive(STAGING_DIR)
        print("Aplicación de la actualización completada.")
    except Exception as e:
        print(f"¡ERROR FATAL AL APLICAR ACTUALIZACIÓN: {e}!")


def run():
    print("--- MODO ACTUALIZACIÓN ---")
    gc.collect()

    if not extract_archive_to_staging(UPDATE_ARCHIVE):
        os.remove(UPDATE_FLAG); machine.reset()
        return

    clean_old_firmware()
    apply_update_from_staging()
    
    print("Limpiando bandera y reiniciando...")
    os.remove(UPDATE_FLAG)
    machine.reset()
