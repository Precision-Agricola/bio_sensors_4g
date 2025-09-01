import typer
from rich import print
from controller_mqtt import actions
from controller_mqtt import commands
import json

app = typer.Typer(help="CLI para enviar comandos a dispositivos Bio-IoT.")

client_app = typer.Typer()
server_app = typer.Typer()
app.add_typer(client_app, name="client", help="Comandos para gestionar el cliente (ESP32).")
app.add_typer(server_app, name="server", help="Comandos para gestionar el servidor (Pico W).")

@client_app.command("update", help="Envía una orden de actualización de firmware al cliente.")
def client_update(
    device: str = typer.Option(..., "--device", "-d", help="ID del dispositivo servidor."),
    version: str = typer.Option(..., "--version", "-v", help="La etiqueta de la release de GitHub. Ej: 'v1.3.0'"),
    repo: str = typer.Option("Precision-Agricola/bio_sensors_4g", "--repo", help="El repositorio de GitHub en formato 'usuario/repo'.")
):
    """Prepara y envía el comando de actualización del cliente."""
    print(f"🤖 Iniciando acción 'update' para el cliente del dispositivo [bold cyan]{device}[/bold cyan]...")
    
    firmware_url = f"https://github.com/{repo}/releases/download/{version}/client.zip"
    print(f"🔗 URL del asset a resolver: {firmware_url}")
    
    actions.handle_update(device, "client", firmware_url)

@server_app.command("update", help="Envía una orden de actualización de firmware al servidor.")
def server_update(
    device: str = typer.Option(..., "--device", "-d", help="ID del dispositivo servidor."),
    version: str = typer.Option(..., "--version", "-v", help="La etiqueta de la release de GitHub."),
    repo: str = typer.Option("Precision-Agricola/bio_sensors_4g", "--repo", help="El repositorio de GitHub.")
):
    """Prepara y envía el comando de actualización del servidor."""
    print(f"🤖 Iniciando acción 'update' para el servidor [bold cyan]{device}[/bold cyan]...")
    
    firmware_url = f"https://github.com/{repo}/releases/download/{version}/server.zip"
    print(f"🔗 URL del asset a resolver: {firmware_url}")

    actions.handle_update(device, "server", firmware_url)

@server_app.command("reboot", help="Envía un comando de reinicio al servidor.")
def server_reboot(
    device:str = typer.Option(..., "--device", "-d", help='ID del server, similar a SERVER_AA12BB'),
):
    """Prepara y envía el comando de reinicio del servidor."""
    print(f"🔄 Iniciando acción 'reboot server' para el dispositivo [bold red]{device}[/bold red]...")
    actions.handle_server_reboot(device=device)
    
@client_app.command("set-params", help="Envía nuevos parámetros de operación al cliente.")
def set_params(
    device: str = typer.Option(..., "--device", "-d"),
    cycle_hours: float = typer.Option(None, "--cycle-hours", help="Duración del ciclo en horas."),
    duty_cycle: float = typer.Option(None, "--duty-cycle", help="Ciclo de trabajo (0.0 a 1.0).")
):
    """Prepara y envía el comando para actualizar parámetros."""
    print(f"🔧 Enviando parámetros al dispositivo [bold cyan]{device}[/bold cyan]...")
    
    params_to_update = {}
    if cycle_hours is not None:
        params_to_update["cycle_hours"] = cycle_hours
    if duty_cycle is not None:
        params_to_update["duty_cycle"] = duty_cycle
    
    if not params_to_update:
        print("[bold yellow]Advertencia: No se especificaron parámetros para actualizar.[/bold yellow]")
        raise typer.Exit()
        
    # actions.handle_set_params(device, params_to_update)
    print(f"Comando 'set-params' con los siguientes datos (implementación pendiente): {params_to_update}")


if __name__ == "__main__":
    app()
