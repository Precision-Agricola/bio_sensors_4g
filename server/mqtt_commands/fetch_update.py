# server/mqtt_commands/fetch_update.py

import uasyncio as asyncio
import ujson
from pico_lte.core import PicoLTE
from pico_lte.utils.status import Status
from utils.logger import log_message
from core.ota_manager import OTAManager
from mqtt_commands.base import MQTTCommand

class FetchUpdateCommand(MQTTCommand):
    """
    Manejador para el comando 'fetch_update'.
    Recibe una URL, descarga los detalles por HTTP y luego inicia el flujo OTA.
    """
    def __init__(self, picoLTE: PicoLTE, ota_manager: OTAManager):
        self.picoLTE = picoLTE
        self.ota_manager = ota_manager
        log_message("FetchUpdateCommand inicializado")

    async def _download_details(self, url: str) -> dict | None:
        """Descarga y parsea el JSON con los detalles del comando."""
        log_message(f"HTTP: Descargando detalles desde {url}")

        try:
            result_url = self.picoLTE.http.set_server_url(url)
            if result_url.get("status") != Status.SUCCESS:
                log_message(f"HTTP: Error al configurar la URL. {result_url.get('response')}")
                return None

            result_get = self.picoLTE.http.get()
            if result_get.get("status") != Status.SUCCESS:
                log_message(f"HTTP: Error al ejecutar GET. {result_get.get('response')}")
                return None
            
            get_urc = self.picoLTE.atcom.get_urc_response("+QHTTPGET: 0,200", timeout=120)
            if get_urc.get("status") != Status.SUCCESS:
                log_message(f"HTTP: No se recibió una respuesta 200 OK. {get_urc.get('response')}")
                return None
            
            result_read = self.picoLTE.http.read_response()
            if result_read.get("status") == Status.SUCCESS:
                response_content = result_read.get("response")
                log_message("HTTP: Descarga de detalles exitosa.")
                
                details = ujson.loads(response_content)
                return details
            else:
                log_message(f"HTTP: Error al leer la respuesta. {result_read.get('response')}")
                return None
        except Exception as e:
            log_message(f"HTTP: Excepción durante la descarga. {e}")
            return None

    def handle(self, payload: dict, topic: str):
        details_url = payload.get('details_url')

        if not details_url:
            log_message("Comando 'fetch_update' inválido: falta 'details_url'.")
            return
        
        asyncio.create_task(self._async_handle(details_url))

    async def _async_handle(self, url: str):
        """Maneja la lógica asíncrona de descarga e inicio del flujo OTA."""
        command_details = await self._download_details(url)
        
        if not command_details:
            log_message("No se pudieron obtener los detalles del comando. Abortando.")
            return
            
        version = command_details.get("version")
        firmware_url = command_details.get("url")
        transfer_params = command_details.get("transfer_params", {})
        ssid = transfer_params.get("ssid")
        password = transfer_params.get("password")

        if not all([version, firmware_url, ssid, password]):
            log_message("Detalles del comando incompletos. Abortando.")
            return
        
        log_message("Iniciando flujo OTA con los detalles descargados.")
        await self.ota_manager.start_update_flow(
            version=version,
            url=firmware_url,
            ssid=ssid,
            password=password
        )
