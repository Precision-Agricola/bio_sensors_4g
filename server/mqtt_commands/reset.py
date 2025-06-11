# server/mqtt_commands/reset.py

import machine
from utils.logger import log_message
from utils.rtc_utils import get_fallback_timestamp
from mqtt_commands.base import MQTTCommand
from core.uart_commands import send_uart_command
from core.aws_forwarding import send_to_aws
from config.device_info import DEVICE_ID

class ResetCommand(MQTTCommand):
    def handle(self, payload, topic):
        log_message(f"⚠️ RESET recibido desde {topic}. Reiniciando...")
        send_uart_command("reset")
        send_to_aws({
            "device_id": DEVICE_ID,
            "event": "command_ack",
            "command_type": "reset",
            "timestamp": get_fallback_timestamp(),
        })

        machine.reset()
