# server/mqtt_commands/params.py

from utils.logger import log_message
from mqtt_commands.base import MQTTCommand

class ParamsCommand(MQTTCommand):
    def handle(self, payload, topic):
        log_message(f"🔧 PARAMS recibidos desde {topic}: {payload}")
        # TODO: Apply the params to the sensor console via uart or wifi
