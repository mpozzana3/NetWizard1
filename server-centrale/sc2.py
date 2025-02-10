import socket
import mysql.connector
import subprocess
import signal
import sys
import json

# Carica la configurazione da file JSON
with open('config2.json', 'r') as f:
    config = json.load(f)

# Parametri del server
HOST = config['server']['host']
PORT = 12346
# Parametri DB MariaDB
DB_HOST = config['database']['db_host']
DB_USER = config['database']['db_user']
DB_PASSWORD = config['database']['db_password']
DB_NAME = config['database']['db_name']

def handle_exit_signal(signal, frame):
    print("\nServer chiuso.")
    sys.exit(0)

signal.signal(signal.SIGINT, handle_exit_signal)  # Gestisce CTRL+C

def create_db_connection():
    """Crea una connessione al database MariaDB."""
    try:
        connection = mysql.connector.connect(
            host=DB_HOST,
            user=DB_USER,
            password=DB_PASSWORD,
            database=DB_NAME,
            charset="utf8mb4",
            collation="utf8mb4_general_ci"
        )
        return connection
    except mysql.connector.Error as e:
        print(f"Errore nella connessione al database: {e}")
        return None

def send_message(client_socket, message):
    """Invia un messaggio al client usando sendall() per evitare troncamenti."""
    client_socket.sendall(message.encode())

def handle_client(client_socket):
    """Gestisce la comunicazione con il client."""
    try:
        dati_ricevuti = client_socket.recv(1024).decode().strip()
        print(f"📩 Dati ricevuti: {dati_ricevuti}")  # Debug
        
        if '|' in dati_ricevuti:
            azienda_choice, p_iva_choice, tipo_scansione = dati_ricevuti.split('|')
        elif dati_ricevuti == '1':
            print("Scelto scansioni, attendo dati successivi...")
            dati_ricevuti = client_socket.recv(1024).decode().strip()
            print(f"📩 Seconda ricezione: {dati_ricevuti}")  # Debug
            
            if '|' in dati_ricevuti:
                azienda_choice, p_iva_choice, tipo_scansione = dati_ricevuti.split('|')
            else:
                send_message(client_socket, "Errore: dati non validi")
                return
        else:
            send_message(client_socket, "Errore: dati non validi")
            return

        print(f"✅ Azienda: {azienda_choice}, P.IVA: {p_iva_choice}, Tipo: {tipo_scansione}")
        
        # --- Ricerca database ---
        db_connection = create_db_connection()
        if db_connection:
            cursor = db_connection.cursor()
            query = "SELECT IP_sonda, Porta_sonda FROM aziende WHERE azienda = %s AND p_iva = %s"
            cursor.execute(query, (azienda_choice, p_iva_choice))
            result = cursor.fetchone()
            db_connection.close()

        if not result:
            send_message(client_socket, "Errore: Azienda non trovata")
            return

        ip_sonda, porta_sonda = result
        print(f"🔄 Connessione alla sonda {ip_sonda}:{porta_sonda}")

        # --- Connessione alla sonda ---
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sonda_socket:
                sonda_socket.connect((ip_sonda, porta_sonda))
                sonda_socket.sendall(tipo_scansione.encode())

                for _ in range(3):
                    response = sonda_socket.recv(1024).decode()
                    print(f"📩 Ricevuto dalla sonda: {response}")
                    send_message(client_socket, response)
        except Exception as e:
            send_message(client_socket, f"Errore nella connessione al server sonda: {e}")
    
    except Exception as e:
        print(f"❌ Errore: {e}")
    finally:
        client_socket.close()

def start_server():
    """Avvia il server e accoglie le connessioni."""
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.bind((HOST, PORT))
    server_socket.listen(5)
    print(f"Server in ascolto su {HOST}:{PORT}...")

    while True:
        client_socket, client_address = server_socket.accept()
        print(f"Connessione stabilita con {client_address}")
        handle_client(client_socket)

if __name__ == "__main__":
    start_server()
