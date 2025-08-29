# controller_mqtt/actions.py

import asyncio
import json
import base64
from rich import print

from .config import AWSIoTConfig
from .commander import IoTCommander
from . import commands

def handle_client_update(device: str, details_url: str):
    """
    Construye, codifica y envía el comando disparador 'fetch_update'.
    """
    commander = None
    try:
        command_dict = commands.create_fetch_update_command(details_url)

        command_json_str = json.dumps(command_dict, separators=(',', ':'))
        base64_bytes = base64.b64encode(command_json_str.encode('utf-8'))
        base64_str = base64_bytes.decode('utf-8')

        wrapper_payload = {"data": base64_str}

        print("🛰️  Realizando conexión con AWS IoT Core...")
        config = AWSIoTConfig()
        commander = IoTCommander(config)
        
        asyncio.run(commander.connect())
        asyncio.run(commander.send_command(wrapper_payload, target_devices=device))
        
        print(f"[bold green]✅ Comando 'fetch_update' enviado exitosamente al dispositivo {device}.[/bold green]")

    except Exception as e:
        print(f"[bold red]❌ ERROR durante la acción de actualización:[/bold red] {e}")
    finally:
        if commander and commander.mqtt_connection:
            print("🔌 Desconectando de AWS IoT Core...")
            asyncio.run(commander.disconnect())

def handle_server_reboot(device: str):
    """
    Construye, conecta y envía el comando de reinicio del servidor usando Base64.
    """
    commander = None
    try:
        command_dict = commands.create_server_reboot_command()
        command_json_str = json.dumps(command_dict, separators=(',', ':'))
        base64_bytes = base64.b64encode(command_json_str.encode('utf-8'))
        base64_str = base64_bytes.decode('utf-8')
        wrapper_payload = {"data": base64_str}

        print("🛰️  Realizando conexión con AWS IoT Core...")
        config = AWSIoTConfig()
        commander = IoTCommander(config)
        
        asyncio.run(commander.connect())
        asyncio.run(commander.send_command(wrapper_payload, target_devices=device))
        
        print(f"[bold green]✅ Comando 'reboot_server' (envuelto en Base64) enviado exitosamente al dispositivo {device}.[/bold green]")

    except Exception as e:
        print(f"[bold red]❌ ERROR durante la acción de reinicio:[/bold red] {e}")
    finally:
        if commander and commander.mqtt_connection:
            print("🔌 Desconectando de AWS IoT Core...")
            asyncio.run(commander.disconnect())
