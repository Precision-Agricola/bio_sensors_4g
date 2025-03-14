"""MQTT Broker para Raspberry Pi Pico W con integración AWS IoT Core

Este script actúa como broker MQTT local y retransmite los datos a AWS IoT Core.
Recibe datos de sensores a través del punto de acceso local y los reenvía a AWS.
"""
import network
import socket
import time
import json
import gc
from machine import Pin
from pico_lte.core import PicoLTE
from pico_lte.common import debug

# Configuración
SSID = "PrecisionAgricola"
PASSWORD = "ag2025pass"
MQTT_PORT = 1883
DEBUG_MODE = True  # Activar depuración detallada

# LED para indicación de estado
led = Pin("LED", Pin.OUT)

# Inicializar PicoLTE para conectividad AWS IoT
picoLTE = PicoLTE()

# Almacenamiento y contadores
received_data = []
message_count = 0
error_count = 0
aws_success_count = 0
aws_error_count = 0
last_device_seen = {}

def debug_print(msg, data=None, force=False):
    """Imprimir información de depuración"""
    if DEBUG_MODE or force:
        print(msg)
        if data is not None:
            if isinstance(data, bytes):
                # Use a simpler approach without list comprehension
                hex_str = ""
                for i in range(min(20, len(data))):
                    hex_str += "{:02x} ".format(data[i])
                if len(data) > 20:
                    hex_str += "..."
                print(f"[BYTES]: {hex_str}")
            else:
                print(f"[DATA]: {data}")

def setup_access_point():
    ap = network.WLAN(network.AP_IF)
    ap.config(essid=SSID, password=PASSWORD)
    ap.active(True)
    
    while not ap.active:
        pass
    
    print("Punto de acceso activo")
    print(f"SSID: {SSID}")
    print(f"Dirección IP: {ap.ifconfig()[0]}")
    return ap

def start_mqtt_broker():
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    s.bind(('0.0.0.0', MQTT_PORT))
    s.listen(5)
    print(f"Broker MQTT escuchando en puerto {MQTT_PORT}")
    return s

def publish_to_aws(data):
    """Publicar datos en AWS IoT Core utilizando PicoLTE"""
    global aws_success_count, aws_error_count
    
    try:
        # Preparar el formato de payload para AWS IoT
        payload_json = {
            "state": {
                "reported": data
            }
        }
        
        debug_print("Enviando datos a AWS IoT:", payload_json)
        
        # Convertir a JSON string
        payload = json.dumps(payload_json)
        
        # Publicar en AWS IoT
        result = picoLTE.aws.publish_message(payload)
        
        if result["status"] == 0:  # Éxito
            aws_success_count += 1
            debug_print("Datos enviados correctamente a AWS IoT", force=True)
            return True
        else:
            aws_error_count += 1
            debug_print("Error al enviar datos a AWS IoT:", result, force=True)
            return False
            
    except Exception as e:
        aws_error_count += 1
        print(f"ERROR AWS: {e}")
        import sys
        sys.print_exception(e)
        return False

def handle_mqtt_packet(payload):
    """Procesar datos de carga útil MQTT recibidos"""
    global message_count
    
    debug_print("Procesando payload:", payload)
    
    try:
        # Decodificar y analizar JSON
        message = payload.decode('utf-8', 'ignore')
        debug_print("Mensaje decodificado:", message)
        
        data = json.loads(message)
        debug_print("JSON parseado con éxito")
        
        # Almacenar los datos
        if len(received_data) >= 100:  # Limitar a 100 mensajes
            received_data.pop(0)
        received_data.append(data)
        
        # Actualizar estadísticas
        message_count += 1
        device_id = data.get("device_id", "unknown")
        last_device_seen[device_id] = time.time()
        
        # Imprimir resumen
        print("\n" + "=" * 40)
        print(f"MENSAJE RECIBIDO #{message_count}")
        print(f"Dispositivo: {device_id}")
        print(f"Timestamp: {data.get('timestamp', 'N/A')}")
        
        # Mostrar datos de sensores - comprobar si usa "sensors" o "data"
        sensor_data = None
        if "sensors" in data:
            sensor_data = data["sensors"]
            print("\nDatos de sensores:")
            for sensor_name, sensor_info in sensor_data.items():
                status = sensor_info.get("status", "Desconocido")
                reading = sensor_info.get("reading", "N/A")
                print(f"  - {sensor_name}: {status}, Valor: {reading}")
        elif "data" in data:
            sensor_data = data["data"]
            print("\nDatos de sensores:")
            for sensor_name, sensor_value in sensor_data.items():
                if isinstance(sensor_value, dict):
                    print(f"  - {sensor_name}: {sensor_value}")
                else:
                    print(f"  - {sensor_name}: Valor: {sensor_value}")
        
        print("=" * 40 + "\n")
        
        # Enviar a AWS IoT Core
        aws_result = publish_to_aws(data)
        if aws_result:
            print("Datos retransmitidos exitosamente a AWS IoT")
        else:
            print("Error al retransmitir datos a AWS IoT")
        
        # Alternar LED
        led.toggle()
        
        return True
    except Exception as e:
        global error_count
        error_count += 1
        print(f"ERROR PROCESANDO MENSAJE: {e}")
        print(f"Payload problemático: {payload}")
        import sys
        sys.print_exception(e)
        return False

def parse_mqtt_packet(packet):
    """Analizar detalladamente un paquete MQTT"""
    if not packet or len(packet) < 2:
        debug_print("Paquete demasiado corto")
        return None, None
        
    cmd = packet[0] & 0xF0
    debug_print(f"Comando MQTT: 0x{cmd:02x}")
    
    # Determinar longitud restante
    multiplier = 1
    remaining_length = 0
    idx = 1
    
    while idx < len(packet):
        byte = packet[idx]
        remaining_length += (byte & 127) * multiplier
        multiplier *= 128
        idx += 1
        if byte & 128 == 0:
            break
    
    debug_print(f"Longitud restante: {remaining_length}, Índice: {idx}")
    
    if cmd == 0x30:  # PUBLISH
        if len(packet) <= idx + 2:
            debug_print("Paquete PUBLISH demasiado corto")
            return None, None
            
        topic_len = (packet[idx] << 8) | packet[idx + 1]
        debug_print(f"Longitud del tema: {topic_len}")
        
        idx += 2
        if len(packet) < idx + topic_len:
            debug_print("Paquete no tiene suficientes bytes para el tema")
            return None, None
            
        topic = packet[idx:idx + topic_len]
        
        idx += topic_len
        
        # QoS puede afectar el desplazamiento
        # Para simplificar, asumimos QoS 0
        
        # El resto es el payload
        if idx < len(packet):
            payload = packet[idx:]
            debug_print(f"Payload encontrado, longitud: {len(payload)}")
            return topic, payload
    
    return None, None

def handle_mqtt(client_socket):
    """Manejar protocolo MQTT básico"""
    try:
        client_socket.settimeout(3)
        packet = client_socket.recv(1024)
        
        debug_print("Paquete recibido:", packet)
        
        if not packet or len(packet) < 2:
            return
        
        # Verificar CONNECT
        if packet[0] == 0x10:
            debug_print("Recibido CONNECT")
            client_socket.write(b"\x20\x02\x00\x00")
            print("Cliente conectado")
            
            # Esperar paquetes PUBLISH
            while True:
                try:
                    packet = client_socket.recv(1024)
                    debug_print("Nuevo paquete recibido:", packet)
                    
                    if not packet or len(packet) < 2:
                        debug_print("Paquete vacío o demasiado corto")
                        break
                    
                    # Verificar si es PUBLISH
                    if (packet[0] & 0xF0) == 0x30:
                        debug_print("Paquete PUBLISH detectado")
                        
                        # Analizar detalladamente
                        topic, payload = parse_mqtt_packet(packet)
                        
                        if payload:
                            debug_print("Payload extraído correctamente")
                            handle_mqtt_packet(payload)
                        else:
                            debug_print("No se pudo extraer payload")
                            
                except Exception as e:
                    print(f"Error leyendo paquete: {e}")
                    import sys
                    sys.print_exception(e)
                    break
    
    except Exception as e:
        print(f"Error de manejo MQTT: {e}")
        import sys
        sys.print_exception(e)
    
    finally:
        try:
            client_socket.close()
        except:
            pass

def print_stats():
    print("\n===== ESTADÍSTICAS DE MENSAJES =====")
    print(f"Mensajes recibidos: {message_count}")
    print(f"Errores de procesamiento: {error_count}")
    print(f"Envíos exitosos a AWS: {aws_success_count}")
    print(f"Errores de envío a AWS: {aws_error_count}")
    print("Últimos dispositivos vistos:")
    
    for device, last_time in last_device_seen.items():
        time_diff = time.time() - last_time
        print(f"  - {device}: hace {time_diff:.1f} segundos")
    
    print("===================================\n")

def main():
    # Inicializar el punto de acceso WiFi
    setup_access_point()
    
    # Inicializar el broker MQTT
    broker_socket = start_mqtt_broker()
    print("Broker MQTT listo - Esperando conexiones")
    print("AWS IoT Core integración activada")
    
    # Timer para estadísticas
    stats_timer = time.time()
    
    # Bucle principal de manejo de conexiones
    while True:
        try:
            # Imprimir estadísticas cada minuto
            if time.time() - stats_timer > 60:
                print_stats()
                stats_timer = time.time()
            
            broker_socket.settimeout(0.5)
            
            try:
                client, addr = broker_socket.accept()
                print(f"Conexión desde {addr}")
                handle_mqtt(client)
            except OSError as e:
                if e.args[0] != 110:  # ETIMEDOUT
                    print(f"Error de socket: {e}")
            
            # Liberación de memoria
            gc.collect()
            
        except Exception as e:
            print(f"Error del servidor: {e}")
            time.sleep(1)

if __name__ == "__main__":
    main()