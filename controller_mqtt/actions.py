# controller_mqtt/actions.py

import asyncio
import json
from rich import print

from .config import AWSIoTConfig
from .commander import IoTCommander
from . import commands

def handle_client_update(device: str, version: str, url: str, ssid: str, password: str):
    """
    Construye, conecta y envía el comando de actualización del cliente.
    """
    commander = None
    try:
        # 1. Construir el payload
        command_payload = commands.create_client_update_command(
            version=version,
            download_url=url,
            wifi_ssid=ssid,
            wifi_pass=password
        )

        # 2. Conectar y enviar
        print("🛰️  Realizando conexión con AWS IoT Core...")
        config = AWSIoTConfig()
        commander = IoTCommander(config)
        
        asyncio.run(commander.connect())
        asyncio.run(commander.send_command(command_payload, target_devices=device))
        
        print(f"[bold green]✅ Comando 'update_client' enviado exitosamente al dispositivo {device}.[/bold green]")

    except Exception as e:
        print(f"[bold red]❌ ERROR durante la acción de actualización:[/bold red] {e}")
    finally:
        # 3. Desconectar
        if commander and commander.mqtt_connection:
            print("🔌 Desconectando de AWS IoT Core...")
            asyncio.run(commander.disconnect())

def handle_server_reboot(device: str):
    """
    Construye, conecta y envía el comando de reinicio del servidor.
    """
    commander = None
    try:

        command_payload = commands.create_server_reboot_command()

        print("🛰️  Realizando conexión con AWS IoT Core...")
        config = AWSIoTConfig()
        commander = IoTCommander(config)
        
        asyncio.run(commander.connect())
        asyncio.run(commander.send_command(command_payload, target_devices=device))
        
        print(f"[bold green]✅ Comando 'reboot_server' enviado exitosamente al dispositivo {device}.[/bold green]")

    except Exception as e:
        print(f"[bold red]❌ ERROR durante la acción de reinicio:[/bold red] {e}")
    finally:
        if commander and commander.mqtt_connection:
            print("🔌 Desconectando de AWS IoT Core...")
            asyncio.run(commander.disconnect())
