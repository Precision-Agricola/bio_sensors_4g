# server/mqtt_commands/update.py

import uasyncio as asyncio
from utils.logger import log_message
from mqtt_commands.base import MQTTCommand
from core.ota_manager import OTAManager


class UpdateClientCommand(MQTTCommand):

    def __init__(self, ota_manager: OTAManager):
        self.ota_manager = ota_manager
        log_message("UpdateClientCommand inicializado")
    
    def handle(self, payload:dict, topic:dict):
        """Extract the detailes of the payload"""
        version = payload.get('version')
        url = payload.get('url')
        transfer_params = payload.get("transfer_params", {})
        ssid = transfer_params.get('ssid')
        password = transfer_params.get("password")

        if not all([version, url, ssid, password]):
            log_message("Uploading payload incompleto")
            return
        
        asyncio.create_task(
            self.ota_manager.start_update_flow(
                version,
                url,
                ssid,
                password
            )
        )
