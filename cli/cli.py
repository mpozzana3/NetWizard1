import click
import requests

# Funzione per inviare un comando di scansione ARP al server
def start_scan_on_server():
    """Invia il comando di avvio della scansione ARP al server."""
    url = "http://localhost:5001/execute"
    data = {
        "command": "start-scan",
        "args": []
    }
    response = requests.post(url, json=data)

    if response.status_code == 200:
        print("Scansione ARP avviata con successo.")
        print(f"Risultati: {response.json().get('result')}")
    else:
        print(f"Errore nell'avvio della scansione ARP: {response.json().get('error', 'Errore sconosciuto')}")

# Funzione per inviare un comando di scansione ARP con intervallo IP al server
def start_scan2_on_server(ip_range):
    """Invia il comando di avvio della scansione ARP con intervallo IP al server."""
    url = "http://localhost:5001/execute"
    data = {
        "command": "start-scan2",
        "args": [ip_range]  # Passa l'intervallo IP come argomento
    }
    response = requests.post(url, json=data)

    if response.status_code == 200:
        print("Scansione ARP con scan-2.py avviata con successo.")
        print(f"Risultati: {response.json().get('result')}")
    else:
        print(f"Errore nell'avvio della scansione ARP: {response.json().get('error', 'Errore sconosciuto')}")

# Funzione per inviare il comando NMAP al server
def start_nmap_scan_on_server(ip_range):
    """Invia il comando NMAP al server."""
    url = "http://localhost:5001/execute"
    data = {
        "command": "start-nmap-scan",
        "args": [ip_range]  # Passa l'intervallo IP come argomento
    }
    response = requests.post(url, json=data)

    if response.status_code == 200:
        print(f"Scansione NMAP avviata per {ip_range}.")
        print(f"Risultati: {response.json().get('result')}")
    else:
        print(f"Errore nell'avvio della scansione NMAP: {response.json().get('error', 'Errore sconosciuto')}")

# Funzione per eseguire comandi nel server
def execute_command(command, args):
    """Invia un comando al server per l'esecuzione."""
    url = "http://localhost:5001/execute"
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

@cli.command()
@click.argument('ip_range', required=True)
def start_scan2(ip_range):
    """Avvia la scansione ARP con scan-2.py per un intervallo IP specifico."""
    start_scan2_on_server(ip_range)

@cli.command()
@click.argument('ip_range', required=True)
def start_nmap(ip_range):
    """Avvia la scansione NMAP per l'intervallo IP specificato."""
    start_nmap_scan_on_server(ip_range)

if __name__ == "__main__":
    cli()
