"""Main mqtt packet for local application"""
import struct
from core.utils import debug_print
def create_publish_packet(topic, payload):
    """Domestic mqtt publish packet"""
    cmd = 0x30
    var_header = struct.pack("!H", len(topic)) + topic.encode()
    remaining_length = len(var_header) + len(payload)
    rl = bytearray()
    while True:
        byte = remaining_length % 128
        remaining_length = remaining_length // 128
        if remaining_length > 0:
            byte |= 0x80
        rl.append(byte)
        if remaining_length == 0:
            break
    packet = bytearray([cmd]) + rl + var_header + payload
    return packet


def parse_mqtt_packet(packet):
    """Analyze mqtt packet"""
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
        debug_print("Tema:", topic)
        
        idx += topic_len
        
        # QoS puede afectar el desplazamiento
        # Para simplificar, asumimos QoS 0
        
        # El resto es el payload
        if idx < len(packet):
            payload = packet[idx:]
            debug_print(f"Payload encontrado, longitud: {len(payload)}")
            return topic, payload
    
    return None, None
