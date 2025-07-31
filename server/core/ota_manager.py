# server/core/ota_manager.py

import uasyncio as asyncio
from utils.logger import log_message

class OTAManager:
    def __init__(self):
        self.update_in_progress = False
        log_message("OTA Manager inicializado.")

    async def start_update_flow(self, version: str, url: str, ssid: str, password: str):
        """
        Simula el flujo completo usando los parámetros recibidos del comando MQTT.
        """
        if self.update_in_progress:
            log_message("OTA: Ya hay una actualización en progreso.")
            return

        self.update_in_progress = True
        log_message(f"OTA: [INICIO] Flujo para versión '{version}'")
        log_message(f"OTA: URL de descarga: {url}")

        try:
            # 1. Simular descarga
            log_message("OTA: [1/5] Simulando descarga de firmware...")
            await asyncio.sleep(5)
            log_message("OTA: [1/5] Descarga simulada completada.")

            # 2. Simular notificación al cliente
            log_message("OTA: [2/5] Simulando notificación al cliente por UART.")
            log_message("--> Comando a enviar por UART: ota_start")
            await asyncio.sleep(1)

            # 3. Simular inicio de servidor local (usando los datos reales)
            log_message(f"OTA: [3/5] Simulando inicio de AP Wi-Fi con SSID: '{ssid}'")
            await asyncio.sleep(2)
            log_message("OTA: [3/5] Servidor local simulado activo.")

            # 4. Simular espera de confirmación
            log_message("OTA: [4/5] Simulando espera de confirmación del cliente...")
            await asyncio.sleep(10)
            log_message("OTA: [4/5] Confirmación simulada recibida del cliente.")

            # 5. Simular limpieza
            log_message("OTA: [5/5] Simulando limpieza...")
            await asyncio.sleep(2)
            log_message("OTA: [5/5] Limpieza simulada completada.")

            log_message(f"OTA: [ÉXITO] Proceso simulado para versión '{version}' completado.")

        except Exception as e:
            log_message(f"OTA: [ERROR] Ocurrió un error en la simulación: {e}")
        finally:
            self.update_in_progress = False
