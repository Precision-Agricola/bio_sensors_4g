# server/mqtt_commands/reset.py

import machine
from utils.logger import log_message
from mqtt_commands.base import MQTTCommand
from core.uart_commands import send_uart_command

class ResetCommand(MQTTCommand):
    def handle(self, payload, topic):
        log_message(f"⚠️ RESET recibido desde {topic}. Reiniciando...")
        send_uart_command("reset")
        machine.reset()
