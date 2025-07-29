# controller_mqtt/cli.py

import json
import typer
from rich import print

from controller_mqtt import actions
from controller_mqtt import commands

app = typer.Typer(help="CLI para enviar comandos a dispositivos Bio-IoT.")

client_app = typer.Typer()
server_app = typer.Typer()
app.add_typer(client_app, name="client", help="Comandos para gestionar el firmware de los Clientes (ESP32).")
app.add_typer(server_app, name="server", help="Comandso para gestionar el firmware de los Servidores" )


@client_app.command("update", help="Envía una orden de actualización de firmware a un cliente.")
def client_update(
    device: str = typer.Option(..., "--device", "-d", help="ID del dispositivo servidor que controla al cliente."),
    version: str = typer.Option(..., "--version", "-v", help="Versión del firmware a instalar. Ej: 'v1.3.0'"),
    url: str = typer.Option(..., "--url", "-u", help="URL completa del archivo client.zip del firmware."),
    ssid: str = typer.Option("PicoUpdateAP", "--ssid", help="SSID para el AP Wi-Fi de transferencia."),
    password: str = typer.Option(..., "--pass", "-p", prompt=True, hide_input=True, help="Contraseña para el AP Wi-Fi."),
    dry_run: bool = typer.Option(False, "--dry-run", help="Muestra el payload del comando sin enviarlo.")
):
    """
    Prepara y delega el comando de actualización del cliente.
    """
    print(f"🤖 Iniciando acción 'update_client' para el dispositivo [bold cyan]{device}[/bold cyan]...")

    if dry_run:
        command_payload = commands.create_client_update_command(version, url, ssid, password)
        print("--- MODO DRY-RUN ---")
        print(json.dumps(command_payload, indent=4))
        raise typer.Exit()

    actions.handle_client_update(
        device=device,
        version=version,
        url=url,
        ssid=ssid,
        password=password
    )

@server_app.command("reboot", help="Envia un comando de reinicio al servidor")
def server_reboot(
    device:str = typer.Option(..., "--device", "-d", help='ID del server, debe verse similar a SERVER_AA12BB'),
    dry_run:bool = typer.Option(False, "--dry-run", help='muestra el payload del comando sin enviarlo')
):
    print(f"Inicando accion 'reboot server' para el dispositivo [bold red] {device} [/bold red]...")

    command_payload = commands.create_server_reboot_command()
    if dry_run:
        print("---MODE DRY RUN---")
        print(json.dumps(command_payload, indent = 4))
        raise typer.Exit 
    
    actions.handle_server_reboot(device=device)

if __name__ == "__main__":
    app()
