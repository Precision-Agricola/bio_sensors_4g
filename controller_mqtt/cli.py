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
    version: str = typer.Option(..., "--version", "-v", help="La etiqueta de la release de GitHub. Ej: 'v1.3.0'"),
    repo: str = typer.Option("Precision-Agricola/bio_sensors_4g", "--repo", help="El repositorio de GitHub en formato 'usuario/repo'."),
    dry_run: bool = typer.Option(False, "--dry-run", help="Muestra el payload del comando sin enviarlo.")
):
    """
    Construye la URL de los detalles y delega el envío del comando 'fetch_update'.
    """
    print(f"🤖 Iniciando acción 'update_client' para el dispositivo [bold cyan]{device}[/bold cyan]...")

    details_url = f"https://github.com/{repo}/releases/download/{version}/details.json"
    print(f"🔗 URL de detalles construida: {details_url}")

    if dry_run:
        command_payload = commands.create_fetch_update_command(details_url)
        print("--- MODO DRY-RUN ---")
        print(json.dumps(command_payload, indent=4))
        raise typer.Exit()

    actions.handle_client_update(
        device=device,
        details_url=details_url
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
