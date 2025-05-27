# controller_mqtt/cli.py

# TODO: use endpoint from .env or similar, same for client-id etc
# TODO: create a tkinter interface

import asyncio
import os
import argparse
import json
from typing import List

from controller_mqtt.config import AWSIoTConfig
from controller_mqtt.commander import IoTCommander
from controller_mqtt import commands # Importa el módulo completo para acceder a las funciones de comandos

async def main():
    parser = argparse.ArgumentParser(
        description="Envía comandos a dispositivos AWS IoT Core.",
        formatter_class=argparse.RawTextHelpFormatter
    )

    parser.add_argument("--endpoint", required=True,
                        help="El endpoint de AWS IoT Core.")
    parser.add_argument("--client-id", default="controller-cli-publisher",
                        help="El ID de cliente MQTT.")

    target_group = parser.add_mutually_exclusive_group(required=True)
    target_group.add_argument("--device", help="ID de un dispositivo específico.")
    target_group.add_argument("--devices",
                        help="Lista de IDs de dispositivos separados por comas (ej: device1,device2).")
    target_group.add_argument("--all", action="store_true",
                        help="Enviar el comando a todos los dispositivos.")

    command_group = parser.add_mutually_exclusive_group(required=True)
    command_group.add_argument("--reset", action="store_true", help="Enviar comando de reinicio.")
    command_group.add_argument("--params", type=str,
                        help="Enviar comando de parámetros (JSON). Ej: '{\"interval\": 60}'")
    command_group.add_argument("--update", type=str, metavar="VERSION[,URL]",
                        help="Enviar comando de actualización. Ej: '1.0.1' o '1.0.2,http://url/fw.bin'")

    args = parser.parse_args()
    script_dir = os.path.dirname(__file__)
    commander = None # Inicializar a None

    try:
        config = AWSIoTConfig(args.endpoint, args.client_id, script_dir)
        print(config)

        commander = IoTCommander(config)
        await commander.connect()

        command_payload = {}
        if args.reset:
            command_payload = commands.create_reset_command()
        elif args.params:
            command_payload = commands.create_params_command(json.loads(args.params))
        elif args.update:
            update_parts = args.update.split(',', 1)
            version = update_parts[0].strip()
            download_url = update_parts[1].strip() if len(update_parts) > 1 else None
            command_payload = commands.create_update_command(version, download_url)

        target: Union[str, List[str]]
        if args.all:
            target = "all"
        elif args.device:
            target = args.device
        elif args.devices:
            target = [d.strip() for d in args.devices.split(',')]

        await commander.send_command(command_payload, target)

    except FileNotFoundError as e:
        print(f"Error de archivo: {e}")
    except json.JSONDecodeError:
        print("Error: El argumento --params no es un JSON válido.")
    except Exception as e:
        print(f"Ocurrió un error: {e}")
    finally:
        if commander:
            await commander.disconnect()

if __name__ == "__main__":
    asyncio.run(main())
