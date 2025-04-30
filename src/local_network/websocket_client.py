import usocket
import ubinascii
import urandom
import uselect
import struct
import re
import uasyncio as asyncio
import config.runtime as runtime_config
import time
from config.secrets import WIFI_CONFIG
from local_network.wifi_manager import connect_wifi
from utils.logger import log_message

MAX_WIFI_ATTEMPTS = 5
WIFI_RETRY_DELAY_S = 5
WIFI_FAIL_WAIT_S = 30
WS_RECONNECT_DELAY_S = 3

SERVER_URI = WIFI_CONFIG.get('ws_server_uri', 'ws://192.168.4.1/ws')

class WebSocketClient:
    def __init__(self, sock):
        self.sock = sock
        self.open = True
        self.poller = uselect.poll()
        self.poller.register(self.sock, uselect.POLLIN)
        self._recv_buffer = b''

    def send(self, message):
        if isinstance(message, str):
            message = message.encode("utf-8")
        fin_opcode = 0x81  # FIN + text frame
        length = len(message)
        mask_bit = 0x80  # Clients must mask payload
        header = bytearray([fin_opcode])
        if length < 126:
            header.append(mask_bit | length)
        elif length < 65536:
            header.append(mask_bit | 126)
            header += struct.pack("!H", length)
        else:
            header.append(mask_bit | 127)
            header += struct.pack("!Q", length)
        # Create a 4-byte mask
        mask = bytearray([urandom.getrandbits(8) for _ in range(4)])
        header += mask
        # Mask payload
        masked = bytearray(message[i] ^ mask[i % 4] for i in range(length))
        self.sock.write(header)
        self.sock.write(masked)
    
    async def _read_exact(self, n_bytes):
        while len(self._recv_buffer) < n_bytes:
            try:
                res = self.poller.poll(1)
                if res:
                    chunk = self.sock.read(n_bytes - len(self._recv_buffer))
                    if chunk is None or chunk == b'':
                        log_message("Connection closed while reading.")
                        self.open = False
                        return None
                    self._recv_buffer += chunk
                else:
                    await asyncio.sleep(0.01)
            except OSError as e:
                log_message(f"OSError during read: {e}")
                if e.args[0] == 113:
                    log_message("Detailed log: ECONNABORTED (113) occurred during socket read.")
                self.open = False
                return None
            except Exception as e:
                log_message(f"Unexpected error during read: {e}")
                self.open = False
                return None

        data = self._recv_buffer[:n_bytes]
        self._recv_buffer = self._recv_buffer[n_bytes:]
        return data

    async def async_recv(self):

        if not self.open:
            return None

        try:
            first_two = await self._read_exact(2)
            if first_two is None: return None
            b1, b2 = struct.unpack("!BB", first_two)

            opcode = b1 & 0x0F
            fin = b1 & 0x80
            if opcode == 0x8: # CLOSE Frame
                 log_message("Received WebSocket CLOSE frame.")
                 self.open = False
                 return None

            payload_len = b2 & 0x7F
            is_masked = b2 & 0x80

            if payload_len == 126:
                ext_len_bytes = await self._read_exact(2)
                if ext_len_bytes is None: return None
                payload_len = struct.unpack("!H", ext_len_bytes)[0]
            elif payload_len == 127:
                ext_len_bytes = await self._read_exact(8)
                if ext_len_bytes is None: return None
                payload_len = struct.unpack("!Q", ext_len_bytes)[0]

            if is_masked:
                log_message("Warning: Received masked frame from server (unexpected).")
                mask = await self._read_exact(4)
                if mask is None: return None
                payload = await self._read_exact(payload_len)
                if payload is None: return None
                # Desenmascarar (¡código no probado!)
                unmasked_payload = bytearray(payload[i] ^ mask[i % 4] for i in range(payload_len))
                payload = bytes(unmasked_payload)
            else:
                payload = await self._read_exact(payload_len)
                if payload is None: return None

            if opcode == 1:
                try:
                    return payload.decode("utf-8")
                except UnicodeError:
                    log_message("Error decoding UTF-8 payload.")
                    return payload
            else:
                return payload

        except Exception as e:
            log_message(f"Exception in async_recv: {e}")
            self.open = False
            return None

    def close(self):
        if self.open:
            try:
                 self.poller.unregister(self.sock)
            except Exception as e:
                 log_message(f"Error unregistering socket from poller: {e}")
        self.open = False
        try:
            self.sock.close()
            log_message("Socket closed.")
        except Exception as e:
            log_message(f"Error closing socket: {e}")

def connect_ws(uri, timeout_sec=10):
    m = re.match(r"ws://([^:/]+)(?::(\d+))?(/.*)?", uri)
    if not m:
        raise ValueError("Invalid WebSocket URI")
    hostname = m.group(1)
    port = int(m.group(2)) if m.group(2) else 80
    path = m.group(3) if m.group(3) else "/"

    sock = None
    try:
        sock = usocket.socket()
        sock.settimeout(timeout_sec)
        addr_info = usocket.getaddrinfo(hostname, port)
        if not addr_info:
            raise OSError(f"Cannot resolve address for {hostname}")
        addr = addr_info[0][-1]
        sock.connect(addr)
        key_bytes = bytearray([urandom.getrandbits(8) for _ in range(16)])
        key = ubinascii.b2a_base64(key_bytes).strip().decode("utf-8")
        handshake = (
            "GET {} HTTP/1.1\r\n"
            "Host: {}:{}\r\n"
            "Upgrade: websocket\r\n"
            "Connection: Upgrade\r\n"
            "Sec-WebSocket-Key: {}\r\n"
            "Sec-WebSocket-Version: 13\r\n"
            "\r\n"
        ).format(path, hostname, port, key)

        sock.write(handshake.encode("utf-8"))
        status_line = sock.readline() # Lee hasta \n
        if not status_line or not status_line.startswith(b"HTTP/1.1 101"):
           raise OSError("WebSocket connection closed or read error") 

        while True:
            header_line = sock.readline()
            if not header_line: # Timeout o cierre inesperado
                raise OSError("WebSocket connection closed or read error")
            if header_line == b"\r\n":
                break

        sock.setblocking(False)
        return WebSocketClient(sock)

    except Exception as e:
        if sock:
            try:
                sock.close()
            except Exception:
                pass
        raise e


async def websocket_client(sensor_routine=None):

    wifi_connection_attempts = 0
    last_wifi_reset_attempt = 0

    while True:
        ws = None
        try:
            if runtime_config.is_reboot_requested():
                log_message("Reboot solicitado, esperando a que el scheduler lo ejecute...")
                await asyncio.sleep(30)
                continue

            log_message("Verificando conectividad WiFi...")
            should_reset_iface = (wifi_connection_attempts == 1) or \
                                 (wifi_connection_attempts > 0 and time.time() - last_wifi_reset_attempt > 300)

            if not connect_wifi(reset_interface=should_reset_iface):
                wifi_connection_attempts += 1
                log_message(f"Fallo al conectar WiFi (Intento {wifi_connection_attempts}/{MAX_WIFI_ATTEMPTS}).")
                if should_reset_iface:
                    last_wifi_reset_attempt = time.time()

                if wifi_connection_attempts >= MAX_WIFI_ATTEMPTS:
                    log_message(f"Se alcanzó el máximo de {MAX_WIFI_ATTEMPTS} intentos fallidos de WiFi.")
                    log_message("Solicitando reinicio coordinado del sistema...")
                    runtime_config.request_reboot()
                    await asyncio.sleep(WIFI_FAIL_WAIT_S)
                else:
                    await asyncio.sleep(WIFI_RETRY_DELAY_S)

                continue

            log_message("WiFi conectado exitosamente.")
            if wifi_connection_attempts > 0: log_message(f"Needed {wifi_connection_attempts} WiFi attempts.")
            wifi_connection_attempts = 0
            runtime_config.clear_reboot_request()
            last_wifi_reset_attempt = 0

            log_message("Intentando conectar al servidor WebSocket:", SERVER_URI)
            ws = connect_ws(SERVER_URI)
            log_message("Conectado al servidor WebSocket!")

            while True:
                msg = await ws.async_recv()
                if msg is None:
                    raise OSError("WebSocket connection closed or read error") # < -- Aquí se daba el error connectionerror

                log_message(f"WS Recibido: {msg}")
                if isinstance(msg, str) and msg.strip().upper() == "PING":
                    log_message("WS Enviado: PONG")
                    ws.send("PONG")
                    if sensor_routine:
                        log_message("Conexión activa, intentando enviar datos pendientes...")
                        sensor_routine.mark_retry_flag()
                #await asyncio.sleep(30)

        except Exception as e:
            log_message(f"Error en ciclo principal WebSocket/WiFi: {e}")
            if ws:
                try:
                    log_message("Cerrando conexión WebSocket en bloque except...")
                    ws.close()
                except Exception as close_err:
                    log_message(f"Error al cerrar WebSocket en except: {close_err}")
            log_message(f"Reintentando ciclo completo en {WS_RECONNECT_DELAY_S} segundos...")
            await asyncio.sleep(WS_RECONNECT_DELAY_S)

async def main(sensor_routine=None):
    asyncio.create_task(websocket_client(sensor_routine))
    while True:
        await asyncio.sleep(1)

if __name__ == '__main__':
    asyncio.run(main())
