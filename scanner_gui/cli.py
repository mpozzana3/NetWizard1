import os
import sys
import json
import socket
import time

SERVER_HOST = "127.0.0.1"
SERVER_PORT = 12346

def load_db_schema():
    """Carica lo schema del database da un file JSON."""
    with open('db_schema.json') as f:
        return json.load(f)

def main():
    print("🔗 Benvenuto, provo a collegarmi al server-centrale...")
    
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.connect((SERVER_HOST, SERVER_PORT))
            print("✅ Sei riuscito a collegarti al server-centrale. Cosa vuoi fare?")
            
            scelta = input("Scegli tra: 1. Analisi 2. Scansioni\n").strip().lower()
            
            if scelta == "scansioni":
                s.sendall("1".encode())
                print("📡 Hai scelto scansioni. Inserisci le informazioni per la scansione.\n")
                
                azienda = input("Azienda: ").strip()
                p_iva = input("Partita IVA: ").strip()
                
                print("Scansioni disponibili: ARP_PASSIVA, ARP_ATTIVA, NMAP, NBTSCAN, ENUM4LINUX, SMBMAP, SMBCLIENT, MASSCAN, COMPLETA")
                scansione = input("Scansione: ").strip()
                
                s.sendall(f"{azienda}|{p_iva}|{scansione}".encode())

                # Attesa per 4 messaggi di risposta dal server
                for i in range(4):
                    response = s.recv(1024).decode().strip()
                    if response:
                        print(f"📩 Ricevuto dal server [{i+1}]: {response}")
                        time.sleep(0.1)  # Simula un'attesa tra i messaggi
                    else:
                        print(f"⚠️ Nessuna risposta ricevuta alla {i+1}ª richiesta.")

            elif scelta == "analisi":
                s.sendall("2".encode())

                schema = load_db_schema()
                tabelle = list(schema['server_centrale'].keys())
                print(f"Tabelle disponibili: {tabelle}")
                
                tabella = input("Tabella da analizzare: ").strip()

                if tabella in schema['server_centrale']:
                    columns = schema['server_centrale'][tabella]
                    column_names = [col['column_name'] for col in columns]
                else:
                    column_names = []

                print(f"Colonne nella tabella: {column_names}")
                colonne = input("Scegli colonne da analizzare, usa virgola per separare (* per tutte): ").strip()

                print("➕ Aggiungi vincolo opzionale (premi INVIO per lasciare vuoto)")
                vincolo = input("Vincolo opzionale (es. id_scansione='1'): ").strip()

                query = f"SELECT {colonne} FROM {tabella}"
                if vincolo:
                    query += f" WHERE {vincolo}"

                print(f"📤 Invio query al server: {query}")
                s.sendall(query.encode())

                # Ricezione della risposta dal server
                response = ''
                total_received = 0  # Per tracciare quanti byte sono stati ricevuti in totale
                while True:
                    chunk = s.recv(4096).decode('utf-8')
                    if not chunk:
                        break
                    response += chunk
                    total_received += len(chunk)
                    print(f"📩 Ricevuto {len(chunk)} byte. Totale ricevuto: {total_received} byte.")

                print(f"✅ Risposta completa ricevuta ({len(response)} byte).")
                print(response)

            s.close()  # Chiude il socket dopo l'uso

    except Exception as e:
        print(f"❌ Errore di connessione: {e}")

if __name__ == "__main__":
    main()
