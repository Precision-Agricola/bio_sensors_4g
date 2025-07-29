# server/core/mqtt_listener.py

import uasyncio as asyncio
import ujson
import machine
from pico_lte.core import PicoLTE
from utils.logger import log_message
from pico_lte.utils.status import Status

from core.ota_manager import OTAManager
from mqtt_commands.params import ParamsCommand
from mqtt_commands.reset import ResetCommand
from mqtt_commands.update import UpdateClientCommand
from config.device_info import DEVICE_ID

def get_mac_suffix():
    mac = machine.unique_id()
    return ''.join('{:02x}'.format(b) for b in mac[-3:]).upper()

SUB_TOPICS = [
    (f"bioiot/control/{DEVICE_ID}", 1),
    ("bioiot/control/all", 1)
]

picoLTE = PicoLTE()

ota_manager = OTAManager()

COMMAND_HANDLERS = {
    "reset": ResetCommand(),
    "params": ParamsCommand(),
    "update_client": UpdateClientCommand(ota_manager=ota_manager),
}

async def listen_for_commands():
    log_message(f"📡 Registrando DEVICE_ID: {DEVICE_ID}")
    log_message("Subscribing to AWS IoT Core...")
    result = picoLTE.aws.subscribe_topics(topics=SUB_TOPICS)

    if result.get("status") != Status.SUCCESS:
        log_message("❌ Suscripción MQTT fallida.")
        return

    log_message("✅ Suscripción MQTT exitosa. Escuchando mensajes...")
    while True:
        try:
            result = picoLTE.aws.read_messages()
            messages = result.get("messages", [])

            for msg in messages:
                topic = msg.get("topic", "")
                raw_message = msg.get("message", "")
                log_message(f"MQTT [{topic}] mensaje recibido: {repr(raw_message)}")

                try:
                    payload_str = raw_message.strip('" \n\r')
                    if not payload_str.endswith("}"):
                        log_message("⏳ Mensaje incompleto. Ignorado.")
                        continue

                    data = ujson.loads(payload_str)
                    command_type = data.get("command_type")
                    payload_data = data.get("payload", {})

                    handler = COMMAND_HANDLERS.get(command_type)
                    if handler:
                        handler.handle(payload_data, topic)
                    else:
                        log_message(f"ℹ️ Comando no reconocido: {command_type}")

                except Exception as e:
                    log_message(f"❌ Error procesando mensaje MQTT: {e}")

            await asyncio.sleep(2)

        except Exception as e:
            log_message(f"❌ Error leyendo mensajes MQTT: {e}")
            await asyncio.sleep(5)
