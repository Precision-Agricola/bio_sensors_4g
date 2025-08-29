# server/mqtt_commands/reset.py

import machine
import uasyncio as asyncio
from utils.logger import log_message
from mqtt_commands.base import MQTTCommand
from core.uart_commands import send_uart_command
from core.aws_forwarding import send_to_aws
from utils.payloads import build_command_ack_payload


class ResetCommand(MQTTCommand):
    def handle(self, _payload: dict, topic: str) -> None:
        log_message("⚠️ RESET recibido desde %s. Reiniciando...", topic)
        send_uart_command("reset")
        asyncio.create_task(send_to_aws(build_command_ack_payload("reset")))
        machine.reset()
