# ufs_to_flash.py – copia UFS → flash Pico (ZIP 40 kB) sin MemoryError
import os, time
from pico_lte.core import PicoLTE
from pico_lte.utils.status import Status

CHUNK       = 256          # bloque principal de lectura
UART_TO_MS  = 15000        # 15 s por operación

lte   = PicoLTE()
file  = lte.file
uart  = lte.atcom.modem_com
at    = lte.atcom

# ───────── helpers optimizados ──────────
def wait_for(token: bytes, timeout=5000):
    """Bloquea hasta ver <token> en el flujo UART; usa ventana de len(token)."""
    win = b''
    t0  = time.ticks_ms()
    while True:
        if time.ticks_diff(time.ticks_ms(), t0) > timeout:
            raise OSError("Timeout esperando " + token.decode())
        b = uart.read(16) or b''           # lee máx. 16 B
        if b:
            win = (win + b)[-len(token):]  # mantiene sólo len(token) bytes
            if win == token:
                return
        else:
            time.sleep_ms(5)

def read_exact(n, timeout=UART_TO_MS):
    buf, t0 = b'', time.ticks_ms()
    while len(buf) < n:
        if time.ticks_diff(time.ticks_ms(), t0) > timeout:
            raise OSError("UART timeout datos")
        buf += uart.read(n - len(buf)) or b''
        time.sleep_ms(2)
    return buf

def read_until(token: bytes):
    """Lee UART hasta que encuentra <token>; buffer máx. 48 B."""
    tail = b''
    while True:
        tail += uart.read(32) or b''
        if len(tail) > 48:
            tail = tail[-48:]              # corta para no crecer
        if token in tail:
            return tail

# ───────── copia principal ──────────
def copy(ufs="UFS:client.zip", dst="/client.zip"):
    name = ufs.split(':')[1]
    info = file.get_file_list(name)
    if info["status"] != Status.SUCCESS:
        raise RuntimeError("No existe en UFS:", name)
    size = int(info["response"][0].split(',')[1])
    print(f"Copiando {name} → {dst}  ({size} bytes)")

    # 1) lanzar QFDWL y esperar CONNECT
    at.send_at_comm_once(f'AT+QFDWL="{ufs}"')
    wait_for(b'CONNECT\r\n', 5000)

    footer_tok = b'\r\n+QFDWL:'
    buf = b''; written = 0
    with open(dst, 'wb') as out:
        while True:
            buf += uart.read(CHUNK) or b''
            idx = buf.find(footer_tok)
            if idx != -1:
                out.write(buf[:idx]); written += idx
                buf = buf[idx+2:]          # descarta CRLF
                break
            if len(buf) > 32:
                out.write(buf[:-32])
                written += len(buf) - 32
                buf = buf[-32:]

        # 3) leer footer hasta OK
        buf += read_until(b'OK\r\n')
        print("Footer:", repr(buf.strip()))

    ok = os.stat(dst)[6] == written
    print("✔ Copia completa." if ok else "⚠ Tamaño distinto.")

if __name__ == "__main__":
    copy()
