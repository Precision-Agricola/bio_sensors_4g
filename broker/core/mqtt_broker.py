"""Local MQTT methods for Broker"""

# core/mqtt_broker.py
import socket
import errno
from core.mqtt_packet import create_publish_packet, parse_mqtt_packet
from core.command_handler import pending_commands
from core.utils import debug_print, handle_received_payload
from core.aws_integration import publish_to_aws

def start_mqtt_broker(port):
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    s.bind(('0.0.0.0', port))
    s.listen(5)
    debug_print(f"Broker MQTT activo en puerto {port}")
    return s

def handle_client(client_socket, stats, led):
    client_socket.settimeout(5)
    try:
        packet = client_socket.recv(1024)
        if not packet or packet[0] != 0x10:  # CONNECT
            return

        client_socket.send(b"\x20\x02\x00\x00")  # CONNACK
        debug_print("Cliente conectado correctamente")

        # Envía comandos pendientes
        for cmd in pending_commands[:]:
            cmd_packet = create_publish_packet(cmd["topic"], cmd["payload"].encode())
            client_socket.send(cmd_packet)
            pending_commands.remove(cmd)

        # Escucha activa con manejo explícito del timeout y desconexión:
        while True:
            try:
                packet = client_socket.recv(1024)
                if not packet:
                    debug_print("Cliente desconectado (recv vacío)")
                    break

                if (packet[0] & 0xF0) == 0x30:  # PUBLISH
                    topic, payload = parse_mqtt_packet(packet)
                    if payload:
                        handle_received_payload(payload, stats, led, publish_to_aws)

            except OSError as e:
                if e.args[0] == errno.ETIMEDOUT:  # tiempo expirado (normal)
                    continue
                elif e.args[0] in [errno.ECONNRESET, errno.ECONNABORTED, errno.ENOTCONN, errno.EPIPE]:
                    debug_print(f"Conexión cliente perdida ({e}). Cerrando socket.")
                    break  # rompe ciclo, cerrará el socket abajo
                else:
                    debug_print(f"OSError inesperado: {e}")
                    break
            except Exception as e:
                debug_print(f"Excepción general inesperada: {e}")
                break

    except Exception as e:
        debug_print(f"Error general del cliente: {e}")
    finally:
        client_socket.close()
        debug_print("Socket cerrado correctamente (finally)")
