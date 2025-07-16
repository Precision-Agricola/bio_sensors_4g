# download_test.py
from pico_lte.core import PicoLTE
from pico_lte.utils.status import Status
import time

# Nombre del archivo en el módem
remote_file = "test.txt"
# Nombre que tendrá el archivo al guardarse en la Pico
local_file = "downloaded_test.txt"

print("Initializing PicoLTE...")
try:
    lte = PicoLTE()
    print("PicoLTE initialized.")

    # --- Paso 1: Descargar el archivo ---
    print(f"Attempting to download '{remote_file}' to '{local_file}'...")
    result = lte.file.download_file_from_modem(remote_file, local_file)

    # --- Paso 2: Verificar el resultado ---
    if result["status"] == Status.SUCCESS:
        print("Download successful!")
        print("Response:", result["response"])
        
        # --- Paso 3: Leer y mostrar el contenido del archivo descargado ---
        print("\n--- Verifying content of local file ---")
        try:
            with open(local_file, "r") as f:
                content = f.read()
                print(f"Content of '{local_file}':")
                print("-------------------------------------")
                print(content)
                print("-------------------------------------")
        except Exception as e:
            print(f"Could not read local file: {e}")

    else:
        print("Download failed.")
        print("Error:", result["response"])

except Exception as e:
    print(f"An unexpected error occurred: {e}")

