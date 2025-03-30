import usocket
import ubinascii
import urandom
import struct
import re
import uasyncio as asyncio
from config.secrets import WIFI_CONFIG
from local_network.wifi import connect_wifi

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
        """Non-blocking receive using polling."""
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

async def websocket_client():
    while True:
        ws = None
        try:
            print("Checking WiFi connectivity...")
            if not connect_wifi():
                print("WiFi not connected. Waiting 5 seconds before retrying...")
                await asyncio.sleep(5)
                continue

            print("WiFi connected. Connecting to", SERVER_URI)
            ws = connect_ws(SERVER_URI)
            print("Connected to WebSocket!")
            while True:
                msg = await ws.async_recv()
                if msg is None:
                    raise Exception("Connection lost (received None)")
                print("Received:", msg)
                if msg.strip() == "PING":
                    ws.send("PONG")
                    print("Sent: PONG")
                await asyncio.sleep(15)
        except Exception as e:
            print("Error:", e, "- reconnecting in 3 seconds...")
            if ws:
                try:
                    ws.close()
                except Exception as close_err:
                    print("Error closing WebSocket:", close_err)
            await asyncio.sleep(3)

async def main():
    asyncio.create_task(websocket_client())
    while True:
        await asyncio.sleep(1)

if __name__ == '__main__':
    asyncio.run(main())
