# server/core/mqtt_listener.py

import uasyncio as asyncio
import ujson
import ubinascii
from pico_lte.core import PicoLTE
from utils.logger import log_message
from pico_lte.utils.status import Status
from core.ota_manager import OTAManager
from mqtt_commands.params import ParamsCommand
from mqtt_commands.reset import ResetCommand
from mqtt_commands.udpate import UpdateCommand 
from config.device_info import DEVICE_ID

SUB_TOPICS = [
    (f"bioiot/control/{DEVICE_ID}", 1),
    ("bioiot/control/all", 1)
]

picoLTE = PicoLTE()
ota_manager = OTAManager(picoLTE)

COMMAND_HANDLERS = {
    "reset": ResetCommand(),
    "params": ParamsCommand(),
    "update": UpdateCommand(ota_manager=ota_manager),
}

async def listen_for_commands():
    log_message(f"📡 Registrando DEVICE_ID: {DEVICE_ID}")
    
    log_message("Conectando a la red celular...")
    picoLTE.network.register_network()
    picoLTE.network.get_pdp_ready()
    
    log_message("Subscribing to AWS IoT Core...")
    result = picoLTE.aws.subscribe_topics(topics=SUB_TOPICS)

    if result.get("status") != Status.SUCCESS:
        log_message("❌ Suscripción MQTT fallida.")
        return

    log_message("✅ Suscripción MQTT exitosa. Escuchando mensajes...")
    
    message_buffer = ""
    while True:
        try:
            result = picoLTE.aws.read_messages()
            messages = result.get("messages", [])

            for msg in messages:
                raw_message = msg.get("message", "")
                if raw_message:
                    message_buffer += raw_message
            
            while '{' in message_buffer and '}' in message_buffer:
                start_index = message_buffer.find('{')
                end_index = message_buffer.find('}')
                
                if end_index > start_index:
                    json_str_wrapper = message_buffer[start_index : end_index + 1]
                    message_buffer = message_buffer[end_index + 1 :]
                    
                    try:
                        wrapper_data = ujson.loads(json_str_wrapper)
                        base64_payload = wrapper_data.get("data")
                        
                        if base64_payload:
                            original_json_str = ubinascii.a2b_base64(base64_payload).decode('utf-8')
                            log_message(f"MQTT [Decodificado]: {original_json_str}")
                            
                            command_data = ujson.loads(original_json_str)
                            command_type = command_data.get("command_type")
                            
                            handler = COMMAND_HANDLERS.get(command_type)
                            if handler:
                                handler.handle(command_data, msg.get("topic", ""))
                            else:
                                log_message(f"ℹ️ Comando no reconocido: {command_type}")

                    except Exception as e:
                        log_message(f"❌ Error procesando/decodificando: {e}")
                else:
                    message_buffer = ""

            await asyncio.sleep(2)
        except Exception as e:
            log_message(f"❌ Error leyendo mensajes MQTT: {e}")
            await asyncio.sleep(5)
