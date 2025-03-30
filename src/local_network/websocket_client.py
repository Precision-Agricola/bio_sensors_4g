import usocket
import ubinascii
import urandom
import struct
import re

class WebSocketClient:
    def __init__(self, sock):
        self.sock = sock
        self.open = True

    def send(self, message):
        if isinstance(message, str):
            message = message.encode("utf-8")
        # Build a text frame (FIN + opcode 1)
        fin_opcode = 0x81
        length = len(message)
        mask_bit = 0x80  # Clients must mask payload
        header = bytearray()
        header.append(fin_opcode)
        if length < 126:
            header.append(mask_bit | length)
        elif length < 65536:
            header.append(mask_bit | 126)
            header += struct.pack("!H", length)
        else:
            header.append(mask_bit | 127)
            header += struct.pack("!Q", length)
        # Generate a 4-byte mask
        mask = bytearray(4)
        for i in range(4):
            mask[i] = urandom.getrandbits(8)
        header += mask
        # Mask payload
        masked = bytearray(length)
        for i in range(length):
            masked[i] = message[i] ^ mask[i % 4]
        self.sock.write(header)
        self.sock.write(masked)

    def recv(self):
        # Read first two bytes of frame header
        first_two = self.sock.read(2)
        if not first_two:
            raise Exception("Connection closed")
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
        # Server messages are not masked so we just decode if text
        if opcode == 1:
            return data.decode("utf-8")
        else:
            return data

    def close(self):
        self.open = False
        self.sock.close()

def connect_ws(uri):
    # Very simple URI parsing (expects ws://host[:port]/path)
    m = re.match(r"ws://([^:/]+)(?::(\d+))?(/.*)?", uri)
    if not m:
        raise Exception("Invalid URI")
    hostname = m.group(1)
    port = int(m.group(2)) if m.group(2) else 80
    path = m.group(3) if m.group(3) else "/"
    sock = usocket.socket()
    addr = usocket.getaddrinfo(hostname, port)[0][-1]
    sock.connect(addr)
    # Generate a random Sec-WebSocket-Key
    key_bytes = bytearray(16)
    for i in range(16):
        key_bytes[i] = urandom.getrandbits(8)
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
    # Check handshake response
    resp = sock.readline()
    if not resp.startswith(b"HTTP/1.1 101"):
        raise Exception("Handshake failed: " + resp.decode("utf-8"))
    while True:
        line = sock.readline()
        if line == b"\r\n":
            break
    return WebSocketClient(sock)

