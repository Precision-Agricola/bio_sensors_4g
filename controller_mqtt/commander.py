import asyncio
import json
from typing import List, Union, Dict, Any
from awscrt import io, mqtt
from awsiot import mqtt_connection_builder
from .config import AWSIoTConfig

class IoTCommander:

    def __init__(self, config: AWSIoTConfig):
        self.config = config
        self.mqtt_connection = None
        self.event_loop_group = None
        self.host_resolver = None
        self.client_bootstrap = None

    async def connect(self):
        if self.mqtt_connection and self.mqtt_connection.is_connected():
            print("Ya conectado al broker MQTT.")
            return

        print(f"Iniciando conexión a {self.config.endpoint}...")
        self.event_loop_group = io.EventLoopGroup(1)
        self.host_resolver = io.DefaultHostResolver(self.event_loop_group)
        self.client_bootstrap = io.ClientBootstrap(self.event_loop_group, self.host_resolver)

        self.mqtt_connection = mqtt_connection_builder.mtls_from_path(
            endpoint=self.config.endpoint,
            cert_filepath=str(self.config.cert_filepath),
            pri_key_filepath=str(self.config.private_key_filepath),
            client_bootstrap=self.client_bootstrap,
            ca_filepath=str(self.config.root_ca_filepath),
            client_id=self.config.client_id,
            clean_session=False, keep_alive_secs=30
        )
        await self.mqtt_connection.connect().result()
        print("¡Conectado exitosamente!")

    async def _publish_command(self, topic: str, command_payload: Dict[str, Any], qos: mqtt.QoS):
        if not self.mqtt_connection or not self.mqtt_connection.is_connected():
            print("Error: No conectado. Llame a connect() primero.")
            return
        message_json = json.dumps(command_payload)
        print(f"Publicando en '{topic}': {message_json}")
        await self.mqtt_connection.publish(topic=topic, payload=message_json, qos=qos).result()
        print("¡Comando publicado!")

    async def send_command(self,
                           command_payload: Dict[str, Any],
                           target_devices: Union[str, List[str]] = "all",
                           qos: mqtt.QoS = mqtt.QoS.AT_LEAST_ONCE):
        if isinstance(target_devices, str):
            topic = self.config.get_topic_for_all_devices() if target_devices == "all" else self.config.get_topic_for_device(target_devices)
            await self._publish_command(topic, command_payload, qos)
        elif isinstance(target_devices, list):
            print(f"Enviando comando a {len(target_devices)} dispositivos...")
            for device_id in target_devices:
                topic = self.config.get_topic_for_device(device_id)
                await self._publish_command(topic, command_payload, qos)
        else:
            print(f"Error: Tipo de 'target_devices' no válido: {type(target_devices)}.")

    async def disconnect(self):
        if self.mqtt_connection and self.mqtt_connection.is_connected():
            print("Desconectando...")
            await self.mqtt_connection.disconnect().result()
            print("Desconectado.")
        else:
            print("No hay conexión activa.")
