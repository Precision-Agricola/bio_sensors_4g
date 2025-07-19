# controller_mqtt/config.py

import os
from pathlib import Path
from dotenv import load_dotenv

class AWSIoTConfig:

    BASE_COMMAND_TOPIC = "bioiot/control"

    def __init__(self):
        """
        El constructor ahora carga la configuración desde un archivo .env
        ubicado en el mismo directorio.
        """
        # Carga las variables de entorno desde el archivo .env
        dotenv_path = Path(os.path.dirname(__file__)) / '.env'
        load_dotenv(dotenv_path=dotenv_path)

        # Lee las variables cargadas
        self.endpoint = os.getenv("AWS_IOT_ENDPOINT")
        self.client_id = os.getenv("DEFAULT_CLIENT_ID", "controller-cli-default")

        # Valida que las variables esenciales existan
        if not self.endpoint:
            raise ValueError("Error: La variable 'AWS_IOT_ENDPOINT' no está definida en tu archivo .env")

        # Calcula las rutas a los certificados de forma relativa al archivo actual
        certs_dir = Path(os.path.dirname(__file__)) / "certs"
        self.cert_filepath = certs_dir / "certificate.pem.crt"
        self.private_key_filepath = certs_dir / "private.pem.key"
        self.root_ca_filepath = certs_dir / "AmazonRootCA1.pem"
        
        self._validate_paths()

    def _validate_paths(self):
        for p in [self.cert_filepath, self.private_key_filepath, self.root_ca_filepath]:
            if not p.is_file():
                raise FileNotFoundError(f"Archivo de certificado no encontrado: {p}")

    def get_topic_for_device(self, device_id: str) -> str:
        return f"{self.BASE_COMMAND_TOPIC}/{device_id}"

    def get_topic_for_all_devices(self) -> str:
        return f"{self.BASE_COMMAND_TOPIC}/all"

    def __str__(self):
        # ... (el método __str__ puede quedar igual o lo puedes quitar si no lo usas)
        return "AWSIoTConfig loaded from .env"