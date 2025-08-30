# /test_remote_updates/list_files.py
from pico_lte.core import PicoLTE
from pico_lte.utils.status import Status

print("--- Script para Listar Archivos en el Módem ---")

try:
    lte = PicoLTE()
    print("Consultando la lista de archivos en el módem (UFS)...")

    # Usamos "*" como comodín para listar todo el contenido del almacenamiento.
    result = lte.file.get_file_list("*")

    if result.get('status') == Status.SUCCESS and result.get('response'):
        print("\nArchivos encontrados:")
        files_found = False
        # El resultado es una lista de strings. Iteramos sobre ella.
        for line in result['response']:
            # Filtramos las líneas que contienen la información del archivo.
            # El formato es: +QFLST: "nombre_archivo",tamaño
            if line.startswith('+QFLST:'):
                files_found = True
                # Extraemos la parte interesante del string.
                info = line.split(':')[1].strip()
                print(f" -> {info}")

        if not files_found:
            # Si el bucle termina sin encontrar ninguna línea +QFLST
            print(" -> No hay archivos en el almacenamiento.")

    else:
        print("\nError al intentar listar los archivos.")
        print("Respuesta del módem:", result.get('response'))

except Exception as e:
    print(f"\n[ERROR FATAL] {e}")

print("\n--- Fin del script ---")
