# download_zip_to_ufs.py  (versión que espera el URC)
from pico_lte.core import PicoLTE
from pico_lte.utils.status import Status

URL       = "https://github.com/Precision-Agricola/bio_sensors_4g/releases/download/test-v0.1.0/client.zip"
UFS_FILE  = "UFS:client.zip"

lte = PicoLTE()

# 0) Asegura que no haya una sesión HTTP previa ocupando el motor
lte.atcom.send_at_comm("AT+QHTTPSTOP")

# 1) Red LTE
lte.network.register_network()
lte.network.get_pdp_ready()

# 2) Configuración HTTP
lte.http.set_context_id(1)
lte.http.set_ssl_context_id(1)

# 3) URL y GET
lte.http.set_server_url(URL)
lte.http.get(timeout=60)                       # devuelve tras el OK

# 4) Esperar URC +QHTTPGET: 0,…
get_urc = lte.atcom.get_urc_response("+QHTTPGET: 0,", timeout=120)
if get_urc["status"] != Status.SUCCESS:
    print("✖ Falló el GET:", get_urc["response"]); raise SystemExit
print("URC:", get_urc["response"][0])          # por ejemplo 200,40981

# 5) Leer y guardar en la UFS
res = lte.http.read_response_to_file(UFS_FILE, timeout=60)
if res["status"] == Status.SUCCESS:
    print("✔ ZIP guardado como", UFS_FILE)
    print("QFLST:", lte.file.get_file_list(UFS_FILE.split(":")[1])["response"])
else:
    print("✖ Falló read_response_to_file:", res["response"])
