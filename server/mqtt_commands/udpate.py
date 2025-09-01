# server/mqtt_commands/update.py

import uasyncio as asyncio
from utils.logger import log_message
from core.ota_manager import OTAManager
from mqtt_commands.base import MQTTCommand

class UpdateCommand(MQTTCommand):
    def __init__(self, ota_manager: OTAManager):
        self.ota_manager = ota_manager
        log_message("UpdateCommand (Simplificado) inicializado")

    def handle(self, payload: dict, topic: str):
        command_payload = payload.get('payload', {})
        target = command_payload.get('target')
        firmware_url = command_payload.get('url')

        if not all([target, firmware_url]):
            log_message("Comando 'update' inválido: faltan 'target' o 'url'.")
            return

        log_message(f"Recibida orden de actualización para '{target}'.")

        asyncio.create_task(
            self.ota_manager.start_update_flow(
                target=target,
                firmware_url=firmware_url
            )
        )
