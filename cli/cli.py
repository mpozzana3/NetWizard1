import os
import sys
import psycopg2
import requests
import click

# Configurazione del database
DB_HOST = "localhost"  # Host del database
DB_NAME = "tirocinio"  # Nome del database
DB_USER = "postgres"  # Nome utente per il database
DB_PASS = "20134"  # Password per l'utente del database

# Funzione per creare la tabella lista_clienti
def create_table():
    """Crea la tabella lista_clienti se non esiste."""
    try:
        conn = psycopg2.connect(host=DB_HOST, database=DB_NAME, user=DB_USER, password=DB_PASS)
        cursor = conn.cursor()
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS lista_clienti (
            id SERIAL PRIMARY KEY,
            nome TEXT NOT NULL,
            piva TEXT NOT NULL UNIQUE
        )
        ''')
        conn.commit()
        cursor.close()
        conn.close()
    except Exception as e:
        print(f"Errore durante la creazione della tabella: {e}")
        sys.exit(1)

# Funzione per aggiungere un cliente
def add_cliente(nome, piva):
    """Aggiunge un cliente alla tabella lista_clienti."""
    try:
        conn = psycopg2.connect(host=DB_HOST, database=DB_NAME, user=DB_USER, password=DB_PASS)
        cursor = conn.cursor()
        cursor.execute("INSERT INTO lista_clienti (nome, piva) VALUES (%s, %s) ON CONFLICT (piva) DO NOTHING", (nome, piva))
        conn.commit()
        if cursor.rowcount > 0:
            print(f"Cliente '{nome}' con P.IVA '{piva}' aggiunto con successo.")
        else:
            print(f"Cliente con P.IVA '{piva}' già esistente.")
        cursor.close()
        conn.close()
    except Exception as e:
        print(f"Errore durante l'inserimento del cliente: {e}")
        sys.exit(1)

# Funzione per inviare richieste al server
def send_request_to_server(command, args=None):
    """Invia un comando al server remoto."""
    url = "http://localhost:5001/execute"
    data = {
        "command": command,
        "args": args or []
    }
    try:
        response = requests.post(url, json=data)
        if response.status_code == 200:
            print(f"Comando '{command}' eseguito con successo.")
            print(f"Risultati: {response.json().get('result')}")
        else:
            print(f"Errore nell'esecuzione del comando '{command}': {response.json().get('error', 'Errore sconosciuto')}")
    except requests.exceptions.RequestException as e:
        print(f"Errore di connessione al server: {e}")

# Funzione per avviare la scansione ARP
def start_scan_on_server():
    """Invia il comando di avvio della scansione ARP al server."""
    send_request_to_server("start-scan")

# Funzione per avviare la scansione ARP con intervallo IP
def start_scan2_on_server(ip_range):
    """Invia il comando di avvio della scansione ARP con intervallo IP al server."""
    send_request_to_server("start-scan2", [ip_range])

# Funzione per avviare la scansione NMAP
def start_nmap_scan_on_server(ip_range):
    """Invia il comando NMAP al server."""
    send_request_to_server("start-nmap-scan", [ip_range])

# Funzione per avviare la scansione completa
def start_scan_completa(ip_range):
    """Esegue tutte le scansioni (ARP passivo, ARP attivo, NMAP) in sequenza."""
    send_request_to_server("start-scan-completa", [ip_range])

@click.group()
def cli():
    """CLI per gestire clienti e scansioni sul server remoto."""
    pass

@cli.command()
def aggiungi_cliente():
    """Aggiunge un cliente al database."""
    create_table()
    print("Inserisci le informazioni del cliente:")
    nome = input("Nome cliente: ").strip()
    piva = input("P.IVA cliente: ").strip()
    add_cliente(nome, piva)

@cli.command()
def scegli_scansione():
    """Seleziona e avvia una scansione sul server remoto."""
    opzioni = [
        ("ARP scanning passivo", "start-scan"),
        ("ARP scanning attivo", "start-scan2"),
        ("NMAP scanning", "start-nmap-scan"),
        ("Scansione completa", "start-scan-completa")
    ]
    print("Seleziona il tipo di scansione:")
    for i, (desc, _) in enumerate(opzioni, start=1):
        print(f"{i}. {desc}")

    while True:
        try:
            scelta = int(input("Inserisci il numero dell'opzione: "))
            if 1 <= scelta <= len(opzioni):
                comando = opzioni[scelta - 1][1]
                if comando == "start-scan2" or comando == "start-nmap-scan":
                    ip_range = input("Inserisci l'intervallo IP (es. 192.168.1.0/24): ").strip()
                    if comando == "start-scan2":
                        start_scan2_on_server(ip_range)
                    elif comando == "start-nmap-scan":
                        start_nmap_scan_on_server(ip_range)
                elif comando == "start-scan-completa":
                    ip_range = input("Inserisci l'intervallo IP per la scansione completa (es. 192.168.1.0/24): ").strip()
                    start_scan_completa(ip_range)
                else:
                    start_scan_on_server()
                break
            else:
                print("Opzione non valida. Riprova.")
        except ValueError:
            print("Inserisci un numero valido.")

if __name__ == "__main__":
    cli()

