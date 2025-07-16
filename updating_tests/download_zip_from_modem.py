# download_test.py
from pico_lte.core import PicoLTE
from pico_lte.utils.status import Status
import time
import os

# Nombre del archivo en el módem
remote_file =  "client.zip"
# Nombre que tendrá el archivo al guardarse en la Pico
local_file = "downloaded_sensors.zip"

print("Initializing PicoLTE...")
try:
    lte = PicoLTE()
    print("PicoLTE initialized.")

    # --- Paso 1: Descargar el archivo ZIP ---
    # Aumentamos el timeout a 60 segundos por ser un archivo más grande.
    print(f"Attempting to download '{remote_file}' to '{local_file}'...")
    result = lte.file.download_file_from_modem(remote_file, local_file, timeout=60*40)

    # --- Paso 2: Verificar el resultado ---
    if result["status"] == Status.SUCCESS:
        print("Download successful!")
        print("Response:", result["response"])
        
        # --- Paso 3: Verificar que el archivo fue creado localmente ---
        # Para un ZIP, no imprimimos el contenido, solo confirmamos que existe.
        print("\n--- Verifying local file ---")
        try:
            # os.stat devuelve información del archivo, si no existe, da un error.
            file_info = os.stat(local_file)
            print(f"File '{local_file}' created successfully.")
            print(f"File size: {file_info[6]} bytes.")
        except Exception as e:
            print(f"Could not verify local file: {e}")

    else:
        print("Download failed.")
        print("Error:", result["response"])

except Exception as e:
    print(f"An unexpected error occurred: {e}")
