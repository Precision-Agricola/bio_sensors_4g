# main.py – Pico W + Sixfab LTE  (MicroPython 1.22)
import network, usocket as socket, time, ubinascii
from pico_lte.core import PicoLTE
from pico_lte.utils.status import Status

# ────────────────────────── CONFIG ────────────────────────── #
AP_SSID, AP_PASS = "PicoLTE_AP", "micropython"
ZIP_NAME = "client.zip"
ZIP_URL  = ("https://raw.githubusercontent.com/Precision-Agricola/"
            "bio_sensors_4g/releases/download/test-v0.1.0/client.zip")

CHUNK  = 2048      # bytes por lectura/envío
DEBUG  = False
# ───────────────────────────────────────────────────────────── #

def dprint(*a):                                   # debug rápido
    if DEBUG: print(*a)

# ──────────────── Clase puente UFS ↔ UART ─────────────────── #
class UFSBridge:
    def __init__(self, lte):
        self.lte   = lte
        self.uart  = lte.atcom.modem_com
        self._buf  = b""                          # sobrante no procesado

    # -- helpers UART ---------------------------------------- #
    def _read_exact(self, n, to_ms=3000):
        data, t0 = b"", time.ticks_ms()
        # consume del buffer interno primero
        if self._buf:
            take = self._buf[:n]; self._buf = self._buf[len(take):]
            data += take
        while len(data) < n:
            if self.uart.any():
                data += self.uart.read(n - len(data))
            elif time.ticks_diff(time.ticks_ms(), t0) > to_ms:
                raise RuntimeError("UART timeout")
        return data

    def _read_until(self, token: bytes, to_ms=3000):
        """Lee hasta incluir 'token'; conserva excedente en self._buf."""
        buf, t0 = self._buf, time.ticks_ms()
        self._buf = b""
        while token not in buf:
            if self.uart.any():
                buf += self.uart.read(self.uart.any())
            elif time.ticks_diff(time.ticks_ms(), t0) > to_ms:
                raise RuntimeError("No apareció", token)
        idx = buf.find(token) + len(token)
        self._buf = buf[idx:]                      # guarda resto
        return buf[:idx]

    # -- comandos AT file ------------------------------------ #
    def open(self, filename):
        rsp = self.lte.atcom.send_at_comm(f'AT+QFOPEN="{filename}",0',
                                          "+QFOPEN:")
        return int(rsp["response"][0].split(":")[1])

    def read(self, handle, length, to_ms=4000):
        """
        Lee exactamente <length> bytes desde la UFS.
        Acepta dos variantes del módem:
          1) ...CRLF CONNECT[ <len>] CRLF <datos> CRLF OK CRLF
          2) ...CRLF <datos> CRLF OK CRLF      (sin línea CONNECT)
        """
        self.uart.write(f"AT+QFREAD={handle},{length}\r")

        # 1 · Eco de la orden
        self._read_until(b"\r\n", to_ms)

        # 2 · Si aparece la palabra CONNECT, descarta esa línea
        try:
            self._read_until(b"CONNECT", 1000)   # prueba rápida
            self._read_until(b"\r\n", 1000)      # fin de línea CONNECT
        except RuntimeError:
            # No hubo CONNECT → es la variante sin cabecera
            pass

        # 3 · Datos binarios
        data = self._read_exact(length, to_ms)

        # 4 · Footer OK
        self._read_until(b"\r\nOK\r\n", to_ms)
        return data

    def close(self, handle):
        self.lte.atcom.send_at_comm(f"AT+QFCLOSE={handle}")

# ──────────────── LTE + descarga ZIP (si falta) ───────────── #
lte = PicoLTE()
ufs = UFSBridge(lte)

def ensure_zip():
    if lte.file._get_file_size(ZIP_NAME) > 0:
        return
    print("Descargando ZIP…")
    lte.atcom.send_at_comm("AT+QHTTPSTOP")
    lte.network.register_network(); lte.network.get_pdp_ready()
    lte.http.set_context_id(1); lte.http.set_ssl_context_id(1)
    lte.http.set_server_url(ZIP_URL); lte.http.get(timeout=60)
    urc = lte.atcom.get_urc_response("+QHTTPGET: 0,", timeout=120)
    if urc["status"] != Status.SUCCESS or not urc["response"][0].startswith("200,"):
        raise RuntimeError("HTTP GET falló")
    res = lte.http.read_response_to_file("UFS:" + ZIP_NAME, timeout=90)
    if res["status"] != Status.SUCCESS:
        raise RuntimeError("Fallo al escribir ZIP")
    print("ZIP guardado.")

ensure_zip()
SIZE  = lte.file._get_file_size(ZIP_NAME)
print("Tamaño ZIP:", SIZE, "bytes")

# ──────────────── CRC-32 para verificar integridad ────────── #
def crc32_ufs():
    h, left = 0, SIZE
    hdl = ufs.open(ZIP_NAME)
    while left:
        chunk = ufs.read(hdl, min(CHUNK, left))
        h = ubinascii.crc32(chunk, h); left -= len(chunk)
    ufs.close(hdl); return h & 0xFFFFFFFF

CRC32 = crc32_ufs()
print("CRC32 UFS:", hex(CRC32))

# ──────────────── Access-Point Wi-Fi ───────────────────────── #
ap = network.WLAN(network.AP_IF)
ap.config(essid=AP_SSID, password=AP_PASS, authmode=3)
ap.active(True)
print("AP listo en", ap.ifconfig()[0])

# ──────────────── Mini-servidor HTTP ───────────────────────── #
srv = socket.socket(); srv.bind(("0.0.0.0", 80)); srv.listen(2)
print("Descarga en: http://192.168.4.1/client.zip")

while True:
    conn, _ = srv.accept()
    conn.readline()
    while conn.readline() != b"\r\n": pass
    conn.write(b"HTTP/1.1 200 OK\r\n"
               b"Content-Type: application/zip\r\n"
               + f"Content-Length: {SIZE}\r\n".encode()
               + f"X-UFS-CRC32: {CRC32}\r\n\r\n".encode())
    try:
        h = ufs.open(ZIP_NAME); sent = 0
        while sent < SIZE:
            chunk = ufs.read(h, min(CHUNK, SIZE - sent))
            conn.write(chunk); sent += len(chunk)
    finally:
        try: ufs.close(h)
        except: pass
        conn.close()
