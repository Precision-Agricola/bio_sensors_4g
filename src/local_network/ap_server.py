# src/local_network/ap_server.py
import network
import socket
import json
from machine import Pin

# Configuración del Access Point
SSID = 'bio_sensors_access_point'
PASSWORD = '#ExitoAgricola1$'
IP = '192.168.1.100'
SUBNET_MASK = '255.255.255.0'
GATEWAY = '192.168.1.100'
PORT = 8080

# Configuración del Access Point
ap = network.WLAN(network.AP_IF)
ap.config(essid=SSID, password=PASSWORD)
ap.config(max_clients=5)  # Hasta 5 dispositivos conectados
ap.ifconfig((IP, SUBNET_MASK, GATEWAY, GATEWAY))
ap.active(True)
print('Access Point activo. IP:', ap.ifconfig()[0])

# Servidor HTTP para recibir datos de sensores
def start_server():
    addr = socket.getaddrinfo('0.0.0.0', PORT)[0][-1]
    s = socket.socket()
    s.bind(addr)
    s.listen(5)
    print('Servidor escuchando en el puerto', PORT)

    while True:
        cl, addr = s.accept()
        print('Conexión desde', addr)
        request = cl.recv(1024)
        request_str = request.decode()

        # Filtrar solicitudes POST
        if "POST" in request_str:
            print("Solicitud POST recibida")
            payload = request_str.split("\r\n\r\n")[1]  # Obtener el cuerpo JSON
            try:
                data = json.loads(payload)
                print("Datos recibidos:", data)
                # Aquí puedes procesar y almacenar los datos
                cl.send('HTTP/1.0 200 OK\r\nContent-type: text/html\r\n\r\n')
                cl.send('Datos recibidos correctamente')
            except Exception as e:
                print("Error al procesar datos:", e)
                cl.send('HTTP/1.0 400 Bad Request\r\nContent-type: text/html\r\n\r\n')
                cl.send('Error en el formato de datos')
        
        cl.close()

# Iniciar el servidor
start_server()
