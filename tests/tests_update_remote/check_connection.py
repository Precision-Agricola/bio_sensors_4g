# /test_remote_updates/check_connection.py
import time
from pico_lte.core import PicoLTE

print("--- Script de Verificación de Conexión ---")

try:
    print("Inicializando comunicación con el módem...")
    lte = PicoLTE()
    print("Módem detectado. Enviando comando AT...")
    
    # Enviar el comando AT y esperar una respuesta
    result = lte.atcom.send_at_comm("AT")
    
    # Verificar si la respuesta contiene "OK"
    if result.get('response') and "OK" in result['response']:
        print("\n¡Éxito! El módem está conectado y responde correctamente.")
        print("Respuesta completa:", result['response'])
    else:
        print("\nError: No se recibió una respuesta 'OK' del módem.")
        print("Respuesta recibida:", result.get('response'))

except Exception as e:
    print(f"\n[ERROR FATAL] No se pudo inicializar la conexión con el módem: {e}")

print("\n--- Fin del script ---")
