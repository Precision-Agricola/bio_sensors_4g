import network
import time
import config.runtime as config

# --- Constantes ---
WIFI_SSID = "PrecisionAgricola"
WIFI_PASSWORD = "ag2025pass"
CONNECTION_TIMEOUT = 15

def connect_wifi(reset_interface=False):
    wlan = network.WLAN(network.STA_IF)

    if reset_interface:
        print("Reiniciando interfaz WiFi...")
        if wlan.active():
            wlan.active(False)
            time.sleep(1)
        wlan.active(True)
        time.sleep(2)

    if not wlan.active():
        print("Activando interfaz WLAN...")
        wlan.active(True)
        time.sleep(1)

    if wlan.isconnected():
        print("WiFi ya está conectado.") # Opcional: Log si ya estaba conectado
        return True

    print(f"Intentando conectar a la red WiFi '{WIFI_SSID}'...")
    try:
        wlan.connect(WIFI_SSID, WIFI_PASSWORD)
    except OSError as e:
        print(f"Error OSError al iniciar conexión: {e}")
        wlan.active(False)
        time.sleep(1)
        wlan.active(True)
        return False

    start_time = time.time()
    while not wlan.isconnected():
        if time.time() - start_time > CONNECTION_TIMEOUT:
            print(f"Error: Timeout ({CONNECTION_TIMEOUT}s) esperando conexión WiFi.")
            try:
                wlan.disconnect()
            except OSError:
                pass
            return False
        time.sleep(1)

    if wlan.isconnected():
        ip_info = wlan.ifconfig()
        print(f"Conectado exitosamente a {WIFI_SSID} con IP: {ip_info[0]}")
        return True
    else:
        # Doble verificación, aunque el timeout debería haberlo capturado
        print("Error: Falló la conexión WiFi después del intento.")
        return False

def is_connected():
    wlan = network.WLAN(network.STA_IF)
    return wlan.active() and wlan.isconnected()

def disconnect_wifi():
    wlan = network.WLAN(network.STA_IF)
    if wlan.isconnected():
        print("Desconectando WiFi...")
        wlan.disconnect()
        time.sleep(1)
    if wlan.active():
        print("Desactivando interfaz WiFi...")
        wlan.active(False)
    print("WiFi desconectada y desactivada.")
