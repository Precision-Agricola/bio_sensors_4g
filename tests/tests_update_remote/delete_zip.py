# /test_remote_updates/delete_zip.py
from pico_lte.core import PicoLTE
from pico_lte.utils.status import Status

# --- Configuración ---
FILE_TO_DELETE = "client.zip"

print(f"--- Script para Borrar el Archivo '{FILE_TO_DELETE}' ---")

try:
    lte = PicoLTE()
    print(f"Intentando borrar el archivo '{FILE_TO_DELETE}' del módem...")
    
    result = lte.file.delete_file_from_modem(FILE_TO_DELETE)
    
    # La biblioteca devuelve SUCCESS si el comando se ejecuta sin errores.
    if result.get('status') == Status.SUCCESS:
        print(f"\n¡Éxito! El archivo '{FILE_TO_DELETE}' ha sido borrado (o no existía).")
    else:
        # Esto podría indicar un problema de permisos o que el archivo está en uso.
        print("\nError: El comando para borrar no se completó correctamente.")
        print("Respuesta del módem:", result.get('response'))

except Exception as e:
    print(f"\n[ERROR FATAL] {e}")

print("\n--- Fin del script ---")
