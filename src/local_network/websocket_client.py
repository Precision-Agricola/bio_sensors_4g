import usocket
import ubinascii
import urandom
import struct
import re
import uasyncio as asyncio
import config.runtime as runtime_config
import time
from config.secrets import WIFI_CONFIG
from local_network.wifi_manager import connect_wifi, is_connected

MAX_WIFI_ATTEMPTS = 5
WIFI_RETRY_DELAY_S = 5
WIFI_FAIL_WAIT_S = 30
WS_RECONNECT_DELAY_S = 3

SERVER_URI = WIFI_CONFIG.get('ws_server_uri', 'ws://192.168.4.1/ws')

class WebSocketClient:
    def __init__(self, sock):
        self.sock = sock
        self.open = True

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

    async def async_recv(self):
        while True:
            first_two = self.sock.read(2)
            if first_two and len(first_two) == 2:
                b1, b2 = struct.unpack("!BB", first_two)
                opcode = b1 & 0x0F
                payload_len = b2 & 0x7F
                if payload_len == 126:
                    ext = self.sock.read(2)
                    payload_len = struct.unpack("!H", ext)[0]
                elif payload_len == 127:
                    ext = self.sock.read(8)
                    payload_len = struct.unpack("!Q", ext)[0]
                data = self.sock.read(payload_len)
                if opcode == 1:
                    return data.decode("utf-8")
                else:
                    return data
            await asyncio.sleep(0.1)

    def close(self):
        self.open = False
        try:
            self.sock.close()
        except Exception as e:
            print("Error closing socket:", e)

def connect_ws(uri):
    m = re.match(r"ws://([^:/]+)(?::(\d+))?(/.*)?", uri)
    if not m:
        raise Exception("Invalid URI")
    hostname = m.group(1)
    port = int(m.group(2)) if m.group(2) else 80
    path = m.group(3) if m.group(3) else "/"
    sock = usocket.socket()
    addr = usocket.getaddrinfo(hostname, port)[0][-1]
    sock.connect(addr)
    sock.setblocking(False)  # switch to non-blocking mode
    # Generate a random Sec-WebSocket-Key
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
    # Wait for handshake response
    while True:
        line = sock.readline()
        if line and line.startswith(b"HTTP/1.1 101"):
            break
        asyncio.sleep(0.1)
    while True:
        line = sock.readline()
        if line == b"\r\n":
            break
    return WebSocketClient(sock)

async def websocket_client(sensor_routine=None):
    """
    Gestiona la conexión WebSocket, incluyendo la conexión WiFi robusta
    y la solicitud de reinicio coordinado en caso de fallo persistente.
    """
    wifi_connection_attempts = 0
    last_wifi_reset_attempt = 0

    while True:
        ws = None
        try:
            if runtime_config.is_reboot_requested():
                print("Reboot solicitado, esperando a que el scheduler lo ejecute...")
                await asyncio.sleep(30)
                continue

            print("Verificando conectividad WiFi...")
            should_reset_iface = (wifi_connection_attempts == 1) or \
                                 (wifi_connection_attempts > 0 and time.time() - last_wifi_reset_attempt > 300)

            if not connect_wifi(reset_interface=should_reset_iface):
                wifi_connection_attempts += 1
                print(f"Fallo al conectar WiFi (Intento {wifi_connection_attempts}/{MAX_WIFI_ATTEMPTS}).")

                if should_reset_iface:
                     last_wifi_reset_attempt = time.time()

                if wifi_connection_attempts >= MAX_WIFI_ATTEMPTS:
                    print(f"Se alcanzó el máximo de {MAX_WIFI_ATTEMPTS} intentos fallidos de WiFi.")
                    print("Solicitando reinicio coordinado del sistema...")
                    runtime_config.request_reboot()
                    await asyncio.sleep(WIFI_FAIL_WAIT_S)
                else:
                    await asyncio.sleep(WIFI_RETRY_DELAY_S)

                continue

            print("WiFi conectado exitosamente.")
            if wifi_connection_attempts > 0:
                 print(f"Se necesitaron {wifi_connection_attempts} intentos para conectar WiFi.")
            wifi_connection_attempts = 0
            runtime_config.clear_reboot_request()
            last_wifi_reset_attempt = 0

            print("Intentando conectar al servidor WebSocket:", SERVER_URI)
            ws = connect_ws(SERVER_URI)
            print("Conectado al servidor WebSocket!")

            while True:
                msg = await ws.async_recv()
                if msg is None:
                    raise ConnectionError("Conexión WebSocket perdida (recv devolvió None)")

                print(f"WS Recibido: {msg}")
                if isinstance(msg, str) and msg.strip().upper() == "PING":
                    print("WS Enviado: PONG")
                    ws.send("PONG")
                    if sensor_routine:
                        print("Conexión activa, intentando enviar datos pendientes...")
                        sensor_routine.mark_retry_flag()
                await asyncio.sleep(30)

        except Exception as e:
            print(f"Error en bucle WebSocket/WiFi: {e}")
            if ws:
                try:
                    print("Cerrando conexión WebSocket...")
                    ws.close()
                except Exception as close_err:
                    print(f"Error al cerrar WebSocket: {close_err}")
            print(f"Reintentando ciclo completo en {WS_RECONNECT_DELAY_S} segundos...")
            await asyncio.sleep(WS_RECONNECT_DELAY_S)

async def main(sensor_routine=None):
    asyncio.create_task(websocket_client(sensor_routine))
    while True:
        await asyncio.sleep(1)

if __name__ == '__main__':
    asyncio.run(main())
