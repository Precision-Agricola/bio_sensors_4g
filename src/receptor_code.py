# Receiver Code - WiFi to RS485 Gateway
from machine import Pin, UART
import network
import usocket as socket
import time
import ujson

# Configuration
RS485_DE = 22
AP_SSID = 'RS485-Gateway'
AP_PASS = 'password123'
UART_PORT = 0

class RS485Forwarder:
    def __init__(self):
        self.uart = UART(UART_PORT, baudrate=9600, tx=Pin(1), rx=Pin(3))
        self.de = Pin(RS485_DE, Pin.OUT)
        self.de.off()

    def send(self, data):
        self.de.on()
        self.uart.write(data)
        time.sleep_ms(10)
        self.de.off()

def create_access_point():
    ap = network.WLAN(network.AP_IF)
    ap.active(True)
    ap.config(essid=AP_SSID, password=AP_PASS)
    print('AP IP:', ap.ifconfig()[0])
    return ap

def web_server(rs485):
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.bind(('', 80))
    s.listen(5)
    print("Esperando conecciones")
    while True:
        conn, addr = s.accept()
        print("Elemento conectado: {addr[0]}")
        try:
            request = conn.recv(1024)
            if b'POST /data' in request:
                # Extract JSON data
                data_start = request.find(b'{')
                data_str = request[data_start:].decode('utf-8')
                data = ujson.loads(data_str)
                
                # Convert hex to bytes and forward
                rs485.send(bytes.fromhex(data['raw']))
                print(f"Forwarded {data['sensor']} data")
                
            conn.send('HTTP/1.1 200 OK\r\n\r\n')
        except Exception as e:
            print("Request error:", e)
        finally:
            conn.close()

def main():
    rs485 = RS485Forwarder()
    ap = create_access_point()
    print("Gateway ready")
    web_server(rs485)

if __name__ == '__main__':
    main()
