# controller_mqtt/config.py
import os
from pathlib import Path

class AWSIoTConfig:

    BASE_COMMAND_TOPIC = "bioiot/control"

    def __init__(self, endpoint: str, client_id: str, script_base_dir: str):
        self.endpoint = endpoint
        self.client_id = client_id
        self.cert_filepath = Path(os.path.join(script_base_dir, "certs", "certificate.pem.crt"))
        self.private_key_filepath = Path(os.path.join(script_base_dir, "certs", "private.pem.key"))
        self.root_ca_filepath = Path(os.path.join(script_base_dir, "certs", "AmazonRootCA1.pem"))
        self._validate_paths()

    def _validate_paths(self):
        for p in [self.cert_filepath, self.private_key_filepath, self.root_ca_filepath]:
            if not p.is_file():
                raise FileNotFoundError(f"Archivo no encontrado: {p}")

    def get_topic_for_device(self, device_id: str) -> str:
        return f"{self.BASE_COMMAND_TOPIC}/{device_id}"

    def get_topic_for_all_devices(self) -> str:
        return f"{self.BASE_COMMAND_TOPIC}/all"

    def __str__(self):
        return (f"--- Configuración AWS IoT ---\n"
                f"  Endpoint: {self.endpoint}\n"
                f"  Client ID: {self.client_id}\n"
                f"  Tópico Base Comandos: {self.BASE_COMMAND_TOPIC}\n"
                f"  Ruta Certificado: {self.cert_filepath}\n"
                f"----------------------------")
