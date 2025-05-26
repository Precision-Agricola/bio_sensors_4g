# server/mqtt_commands/reset.py

import machine
from utils.logger import log_message
from mqtt_commands.base import MQTTCommand

class ResetCommand(MQTTCommand):
    def handle(self, payload, topic):
        log_message(f"⚠️ RESET recibido desde {topic}. Reiniciando...")
        machine.reset()
        # TODO: Request the restart to the sensor console too (uart)
