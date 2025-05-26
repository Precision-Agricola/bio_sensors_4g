# server/mqtt_commands/update.py

from utils.logger import log_message
from mqtt_commands.base import MQTTCommand

class UpdateCommand(MQTTCommand):
    def handle(self, payload, topic):
        version = payload.get("version", "unknown")
        url = payload.get("download_url", None)

        log_message(f"⬇️ ACTUALIZACIÓN solicitada desde {topic} -> Versión: {version}")
        if url:
            log_message(f"🔗 URL para descargar firmware: {url}")
            # TODO: Implement update logic
