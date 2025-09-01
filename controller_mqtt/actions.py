# controller_mqtt/actions.py

import asyncio
import json
import base64
from rich import print
import requests
from .config import AWSIoTConfig
from .commander import IoTCommander
from . import commands

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


def handle_update(device: str, target: str, asset_url: str):
    """
    Resuelve la URL del asset para obtener el enlace de descarga directo y
    luego envía el comando de actualización a la Pico.
    """
    commander = None
    try:
        # 1. Resolver la URL para seguir la redirección
        print(f"🔎 Resolviendo URL del asset: {asset_url}")
        response = requests.head(asset_url, allow_redirects=True, timeout=10)
        response.raise_for_status()  # Lanza un error si la URL da 404, etc.
        final_download_url = response.url
        print(f"✅ URL directa obtenida: {final_download_url}")
        
        # 2. Construir el comando MQTT con la URL final
        command_dict = commands.create_update_command(target, final_download_url)

        # 3. Codificar en Base64 y envolver
        command_json_str = json.dumps(command_dict, separators=(',', ':'))
        base64_bytes = base64.b64encode(command_json_str.encode('utf-8'))
        base64_str = base64_bytes.decode('utf-8')
        wrapper_payload = {"data": base64_str}

        # 4. Conectar y enviar el comando
        print(f"🛰️  Enviando comando de actualización para '{target}' a {device}...")
        config = AWSIoTConfig()
        commander = IoTCommander(config)
        asyncio.run(commander.connect())
        asyncio.run(commander.send_command(wrapper_payload, target_devices=device))
        print(f"[bold green]✅ Comando enviado exitosamente.[/bold green]")

    except requests.exceptions.RequestException:
        print(f"[bold red]❌ ERROR: No se pudo resolver la URL del asset. Verifica la red o que la versión '{asset_url.split('/')[-2]}' exista.[/bold red]")
    except Exception as e:
        print(f"[bold red]❌ ERROR durante la acción de actualización:[/bold red] {e}")
    finally:
        if commander:
            print("🔌 Desconectando de AWS IoT Core...")
            asyncio.run(commander.disconnect())
