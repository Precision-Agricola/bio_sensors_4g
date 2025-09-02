# server/core/ota_manager.py

import time
import uasyncio
import network
import socket
import gc
import os
import ubinascii
import machine
from pico_lte.core import PicoLTE
from pico_lte.utils.status import Status
from utils.logger import log_message
from core.uart_manager import send_uart_command_async

class OTAManager:
    def __init__(self, picoLTE: PicoLTE):
        self.picoLTE = picoLTE
        self.update_in_progress = False
        log_message("OTA Manager inicializado.")

    async def start_update_flow(self, target: str, firmware_url: str):
        if self.update_in_progress:
            log_message("OTA: Actualización ya en progreso.")
            return

        self.update_in_progress = True
        firmware_filename = f"{target}.zip"
        log_message(f"OTA: [INICIO] Flujo para actualizar '{target}'")
        
        try:
            log_message(f"OTA [1/3]: Descargando {firmware_filename}...")
            if not await self._download_file_to_modem(firmware_url, firmware_filename):
                raise Exception("Fallo en la descarga del firmware")
            log_message("OTA [1/3]: Descarga completada.")

            if target == 'client':
                log_message("OTA [2/3]: Preparando para transferencia local a cliente...")
                # La función _transfer_zip_to_client es síncrona/bloqueante en su núcleo,
                # pero la llamamos con 'await' para que encaje en el flujo asíncrono.
                if not await self._transfer_zip_to_client(firmware_filename):
                    raise Exception("Fallo en la transferencia local al cliente")
                log_message("OTA [2/3]: Transferencia local finalizada.")
            elif target == 'server':
                log_message("OTA [2/3]: Lógica de actualización del servidor (por implementar).")
                await uasyncio.sleep(5)

            log_message("OTA [3/3]: Limpiando archivos...")
            self.picoLTE.file.delete_file_from_modem(firmware_filename)
            log_message("OTA [3/3]: Limpieza completada.")
            log_message(f"OTA: [ÉXITO] Proceso para '{target}' finalizado.")

        except Exception as e:
            log_message(f"OTA: [ERROR] {e}")
        finally:
            self.update_in_progress = False

    async def _download_file_to_modem(self, url: str, filename: str) -> bool:
        # Esta función no requiere cambios.
        ufs_path = f"UFS:{filename}"
        log_message(f"HTTP: Usando método de descarga directa para {filename}")
        
        try:
            self.picoLTE.file.delete_file_from_modem(filename)
            self.picoLTE.atcom.send_at_comm("AT+QHTTPSTOP")
            
            self.picoLTE.http.set_context_id(1)
            self.picoLTE.http.set_ssl_context_id(1)
            self.picoLTE.http.set_server_url(url)
            self.picoLTE.http.get(timeout=60)
            
            get_urc = self.picoLTE.atcom.get_urc_response("+QHTTPGET: 0,", timeout=120)
            if get_urc["status"] != Status.SUCCESS:
                log_message(f"HTTP: Falló la petición GET inicial. {get_urc.get('response')}")
                return False
            
            response_str = get_urc.get("response", [""])[0]
            parts = response_str.split(',')
            if len(parts) > 1:
                http_status_code = int(parts[1])
                log_message(f"HTTP: El servidor respondió con el código {http_status_code}.")
                if not (200 <= http_status_code < 400):
                    log_message(f"HTTP: Código de estado de error ({http_status_code}). Abortando descarga.")
                    return False
            else:
                log_message("HTTP: No se pudo parsear el código de estado de la respuesta URC.")
                return False

            res = self.picoLTE.http.read_response_to_file(ufs_path, timeout=180)
            return res["status"] == Status.SUCCESS
        except Exception as e:
            log_message(f"HTTP: Excepción durante la descarga. {e}")
            return False

    async def _transfer_zip_to_client(self, filename: str) -> bool:
        ap = None
        server_socket = None
        client_socket = None
        success = False
        uart = self.picoLTE.atcom.modem_com
        DEFAULT_RXBUF_SIZE = 2048 # Tamaño original del búfer de la librería

        try:
            # 1. FORZAR RECOLECCIÓN DE BASURA
            # Limpiamos la memoria fragmentada por la descarga HTTP ANTES de
            # intentar asignar un bloque de memoria grande.
            gc.collect()

            # 2. AUMENTAR EL BÚFER A UN TAMAÑO SEGURO
            # 4KB es un compromiso: suficiente para evitar el desbordamiento,
            # y con alta probabilidad de ser asignado sin error de memoria.
            LARGER_RXBUF_SIZE = 4096
            uart.init(rxbuf=LARGER_RXBUF_SIZE)
            log_message(f"OTA: Búfer UART aumentado temporalmente a {LARGER_RXBUF_SIZE} bytes.")
            
            # --- Lógica de transferencia ---
            pico_id = ubinascii.hexlify(machine.unique_id()).decode('utf-8')
            dynamic_ssid = f"OTA_PICO_{pico_id[-6:]}"
            # Usamos una contraseña fija para las pruebas, como solicitaste.
            dynamic_pass = "password123"
            # dynamic_pass = ubinascii.hexlify(os.urandom(8)).decode('utf-8') # <- Opción para producción
            
            log_message(f"OTA: Credenciales dinámicas -> SSID: {dynamic_ssid}")

            command_to_send = {
                "command_type": "ota_start",
                "payload": {"ssid": dynamic_ssid, "password": dynamic_pass}
            }
            await send_uart_command_async(command_to_send)
            
            ap = await self._setup_access_point_async(dynamic_ssid, dynamic_pass)
            log_message("OTA: Access Point creado. Esperando conexión del cliente...")
            
            addr = socket.getaddrinfo('0.0.0.0', 80)[0][-1]
            server_socket = socket.socket()
            server_socket.bind(addr)
            server_socket.listen(1)
            
            client_socket, addr = server_socket.accept()
            log_message(f"OTA: Cliente conectado desde {addr}")

            file_size = self._check_modem_file(filename)
            if not file_size:
                raise Exception(f"El archivo {filename} no se encontró en el módem.")

            success = self._stream_file_to_client(client_socket, file_size, filename)
            
        except Exception as e:
            log_message(f"OTA: Error durante la transferencia local: {e}")
            success = False
        finally:
            # 3. RESTAURACIÓN SEGURA DEL BÚFER
            # Es crucial restaurar el búfer a su tamaño original para liberar memoria,
            # sin importar si la transferencia tuvo éxito o falló.
            uart.init(rxbuf=DEFAULT_RXBUF_SIZE)
            log_message(f"OTA: Búfer UART restaurado a {DEFAULT_RXBUF_SIZE} bytes.")

            # --- Limpieza de recursos ---
            if client_socket: client_socket.close()
            if server_socket: server_socket.close()
            if ap and ap.active():
                ap.active(False)
                log_message("OTA: Access Point desactivado.")
            gc.collect() # Limpieza final
            
        return success


    async def _setup_access_point_async(self, ssid: str, password: str):
        ap = network.WLAN(network.AP_IF)
        ap.config(essid=ssid, password=password)
        ap.active(True)
        while not ap.active():
            await uasyncio.sleep_ms(100) # Corregido: uasyncio
        return ap

    def _check_modem_file(self, filename: str) -> int | None:
        # Esta función no requiere cambios.
        result = self.picoLTE.file.get_file_list(filename)
        if result.get('status') == Status.SUCCESS and result.get('response'):
            for line in result['response']:
                if line.startswith('+QFLST:'):
                    try:
                        parts = line.split(',')
                        filename_part = parts[0].split(':')[1].strip().strip('"')
                        filesize = parts[1].strip()
                        if filename_part == filename:
                            return int(filesize)
                    except (IndexError, ValueError):
                        continue
        return None

    def _stream_file_to_client(self, client_socket, file_size: int, filename: str) -> bool:
        """
        Transmite el archivo replicando la lógica exacta del script de prueba
        para máxima fiabilidad, incluyendo el bucle de limpieza final.
        """
        uart = self.picoLTE.atcom.modem_com

        try:
            client_socket.sendall(b'HTTP/1.1 200 OK\r\n')
            client_socket.sendall(b'Content-Type: application/zip\r\n')
            client_socket.sendall(f'Content-Length: {file_size}\r\n'.encode())
            client_socket.sendall(b'Content-Disposition: attachment; filename="client.zip"\r\n')
            client_socket.sendall(b'Connection: close\r\n\r\n')

            command = f'AT+QFDWL="{filename}"\r\n'
            if uart.any(): uart.read()
            uart.write(command.encode('utf-8'))
            
            connect_found = False
            start_time = time.ticks_ms()
            buffer = b''
            while time.ticks_diff(time.ticks_ms(), start_time) < 5000:
                if uart.any():
                    buffer += uart.read(1)
                    if b'\n' in buffer:
                        line = buffer.strip().decode('utf-8', 'ignore')
                        if "CONNECT" in line:
                            connect_found = True
                            break
                        buffer = b''
            
            if not connect_found:
                log_message("OTA: Timeout, no se recibió 'CONNECT' del módem.")
                return False

            log_message(f"OTA: Iniciando streaming de {file_size} bytes...")

            bytes_sent = 0
            chunk_size = 2048
            gc.collect()

            while bytes_sent < file_size:
                bytes_to_read = min(chunk_size, file_size - bytes_sent)
                chunk_data = uart.read(bytes_to_read)
                
                if not chunk_data:
                    log_message(f"OTA ERROR: La lectura de UART falló en {bytes_sent} bytes.")
                    return False
                
                client_socket.write(chunk_data)
                bytes_sent += len(chunk_data)

            log_message(f"OTA: Streaming finalizado. Total enviado: {bytes_sent} bytes.")

            cleanup_start_time = time.ticks_ms()
            while time.ticks_diff(time.ticks_ms(), cleanup_start_time) < 3000:
                if uart.any():
                    response_bytes = uart.read()
                    if response_bytes and b"OK" in response_bytes:
                        break
            
            return bytes_sent == file_size

        except Exception as e:
            log_message(f"OTA: Excepción durante el streaming: {e}")
            return False
        finally:
            client_socket.close()
            log_message("OTA: Conexión del cliente cerrada.")
