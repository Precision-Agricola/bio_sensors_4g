# serve_ufs_zip.py  (corre en la Pico W, con el módem inicializado)
from pico_lte.core import PicoLTE
import usocket as socket

ZIP_PATH = "UFS:client.zip"       # mismo nombre que usaste al grabar
CHUNK    = 2048                   # bytes a leer por iteración

lte   = PicoLTE()
size  = lte.file._get_file_size(ZIP_PATH.split(":")[1])   # ← usa el helper privado

if size <= 0:
    raise RuntimeError("No se pudo obtener el tamaño del ZIP.")

s = socket.socket()
s.bind(("0.0.0.0", 80))           # la Pico W ya está como AP (192.168.4.1)
s.listen(1)

while True:
    conn, _ = s.accept()
    conn.readline()               # “GET /…”
    while conn.readline() != b"\r\n":   # descarta cabeceras del cliente
        pass

    conn.write(b"HTTP/1.1 200 OK\r\n"
               b"Content-Type: application/zip\r\n"
               + f"Content-Length: {size}\r\n\r\n".encode())

    offset = 0
    while offset < size:          # stream directo UFS → Wi-Fi
        res = lte.file.read_file(ZIP_PATH, offset, CHUNK)
        if res["status"] != 0:    # 0 = SUCCESS en el SDK
            print("Error de lectura:", res); break
        data = res["response"]
        conn.write(data)
        offset += len(data)

    conn.close()
