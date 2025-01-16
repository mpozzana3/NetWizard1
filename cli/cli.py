import click
import subprocess
import sys
import requests

# Funzione per inviare un comando di scansione al server tramite HTTP
def start_scan_on_server():
    """Invia il comando di avvio della scansione ARP al server."""
    url = "http://localhost:5000/execute"
    data = {
        "command": "start_scan",
        "args": []
    }
    response = requests.post(url, json=data)
    
    if response.status_code == 200:
        print("Scansione ARP avviata con successo.")
    else:
        print(f"Errore nell'avvio della scansione ARP: {response.json().get('error', 'Errore sconosciuto')}")

# Funzione per eseguire comandi nel server
def execute_command(command, args):
    """Invia un comando al server per l'esecuzione."""
    url = "http://localhost:5000/execute"
    data = {
        "command": command,
        "args": args
    }
    
    try:
        response = requests.post(url, json=data)
        if response.status_code == 200:
            print(f"Risultato: {response.json().get('result')}")
        else:
            print(f"Errore: {response.json().get('error')}")
    except requests.exceptions.RequestException as e:
        print(f"Errore di connessione: {e}")

@click.group()
def cli():
    """CLI per gestire la scansione e l'esecuzione di comandi sul server."""
    pass

@cli.command()
@click.argument('command')
@click.argument('args', nargs=-1)
def execute(command, args):
    """Esegui un comando sul server."""
    execute_command(command, args)

@cli.command()
def start_scan():
    """Avvia la scansione ARP sulla rete del server."""
    start_scan_on_server()

if __name__ == "__main__":
    cli()
