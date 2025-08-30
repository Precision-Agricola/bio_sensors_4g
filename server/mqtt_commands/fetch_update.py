# server/mqtt_commands/fetch_update.py

import uasyncio as asyncio
import ujson
import uos
from pico_lte.core import PicoLTE
from pico_lte.utils.status import Status
from utils.logger import log_message
from core.ota_manager import OTAManager
from mqtt_commands.base import MQTTCommand

class FetchUpdateCommand(MQTTCommand):
    def __init__(self, picoLTE: PicoLTE, ota_manager: OTAManager):
        self.picoLTE = picoLTE
        self.ota_manager = ota_manager
        log_message("FetchUpdateCommand inicializado")

    async def _download_details(self, url: str) -> dict | None:
        """Descarga y parsea el JSON con los detalles del comando."""
        log_message(f"HTTP: Descargando detalles desde {url}")
        details_filename = "details.json"
        
        try:
            self.picoLTE.http.set_server_url(url)
            self.picoLTE.http.get()
            get_urc = self.picoLTE.atcom.get_urc_response("+QHTTPGET: 0,200", timeout=120)
            if get_urc.get("status") != Status.SUCCESS:
                log_message(f"HTTP: No se recibió 200 OK. {get_urc.get('response')}")
                return None
            
            result_read = self.picoLTE.http.read_response_to_file(details_filename)
            if result_read.get("status") != Status.SUCCESS:
                log_message(f"HTTP: Error al guardar el archivo. {result_read.get('response')}")
                return None

            log_message(f"HTTP: Archivo '{details_filename}' guardado temporalmente.")
 
            with open(details_filename, "r") as f:
                details = ujson.load(f)
            return details

        except Exception as e:
            log_message(f"HTTP: Excepción durante la descarga. {e}")
            return None
        finally:
            try:
                uos.remove(details_filename)
                log_message(f"HTTP: Archivo temporal '{details_filename}' borrado.")
            except OSError:
                pass

    def handle(self, payload: dict, topic: str):
        command_payload = payload.get('payload', {})
        details_url = command_payload.get('details_url')

        if not details_url:
            log_message("Comando 'fetch_update' inválido: falta 'details_url'.")
            return
        
        asyncio.create_task(self._async_handle(details_url))

    async def _async_handle(self, url: str):
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
