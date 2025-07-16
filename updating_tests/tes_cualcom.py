# serve_zip_microdot.py
#
# Sirve "bio_sensors_v1_4.zip" directamente desde la UFS del BG95-B.
# 1. Asegúrate de que existe como "UFS:bio_sensors_v1_4.zip".
# 2. Ejecuta:  import serve_zip_microdot
# 3. Conéctate al AP  SSID: pico_zip  PASS: zipdownload
# 4. Descarga:       http://192.168.4.1/releases/bio_sensors_v1_4.zip
#
# Framework: microdot-micropython  (pon microdot.py en el FS si no lo tienes).

import time, socket, network
from microdot import Microdot, Response
from pico_lte.core import PicoLTE
from pico_lte.utils.status import Status

# ───────── Parámetros ──────────────────────────────────────────────────────
ZIP_UFS  = "UFS:bio_sensors_v1_4.zip"
URL_PATH = "/releases/bio_sensors_v1_4.zip"
CHUNK    = 1024
SSID     = "pico_zip"
PASSWORD = "zipdownload"
# ───────────────────────────────────────────────────────────────────────────

#############################################################################
# 1. Módem y tamaño
#############################################################################
lte = PicoLTE()
resp = lte.file.get_file_list(ZIP_UFS.split(":")[1])
if resp["status"] != Status.SUCCESS or not resp["response"]:
    raise RuntimeError("ZIP no encontrado en UFS")
FILE_SIZE = int(resp["response"][0].split(",")[1])
print("ZIP size:", FILE_SIZE, "bytes")

#############################################################################
# 2. AP Wi-Fi
#############################################################################
ap = network.WLAN(network.AP_IF)
ap.active(True)
ap.config(essid=SSID, password=PASSWORD)   # WPA2-PSK implícito
HOST_IP = ap.ifconfig()[0]
print("AP listo →", HOST_IP)


SMALL_FILE = "UFS:test.txt"

#############################################################################
# 3. Utilidades de lectura
#############################################################################
def read_exact(uart, n, t_ms=8000):
    buf = b''
    t0 = time.ticks_ms()
    while len(buf) < n:
        if time.ticks_diff(time.ticks_ms(), t0) > t_ms:
            raise OSError("UART timeout")
        chunk = uart.read(n - len(buf)) or b''
        if chunk:
            buf += chunk
        else:
            time.sleep_ms(5)
    return buf

def ufs_iter():
    at = lte.atcom
    handle = int(at.send_at_comm(f'AT+QFOPEN="{ZIP_UFS}",0',
                   "+QFOPEN:")["response"][0].split(":")[1])
    sent = 0
    try:
        while sent < FILE_SIZE:
            n = min(CHUNK, FILE_SIZE - sent)
            at.send_at_comm(f"AT+QFREAD={handle},{n}",
                            "CONNECT", urc=True, timeout=30)
            data = read_exact(at.modem_com, n)
            at.get_response("OK", timeout=5)
            sent += n
            yield data
    finally:
        at.send_at_comm(f"AT+QFCLOSE={handle}")

#############################################################################
# 4. Servidor Microdot
#############################################################################
app = Microdot()
Response.default_content_type = 'text/plain'

@app.get(URL_PATH)
def send_zip(req):
    hdrs = [
        ('Content-Type',  'application/zip'),
        ('Content-Length', str(FILE_SIZE)),
        ('Connection', 'close')
    ]
    return Response(ufs_iter(), 200, hdrs)

@app.get('/')
def index(req):
    return f"Descarga ZIP → http://{HOST_IP}{URL_PATH}\n"

@app.route('<path:path>')
def not_found(req, path):
    return Response('Not Found', 404)

@app.get('/test.txt')
def send_txt(req):
    size = len(dummy)          # lo sabes si acabas de crearlo
    headers = [('Content-Type', 'text/plain'),
               ('Content-Length', str(size)),
               ('Connection', 'close')]
    def gen():
        yield dummy
    return Response(gen(), 200, headers)

print(f"Sirviendo en http://{HOST_IP}{URL_PATH}")
app.run(host='0.0.0.0', port=80)
