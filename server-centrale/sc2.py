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

def execute_query(query):
    """Esegue mariadbquery.py con una query e restituisce il risultato."""
    try:
        process = subprocess.Popen(["python3", "mariadbquery.py", query], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        stdout, stderr = process.communicate()
        return stdout if stdout else stderr
    except Exception as e:
        return f"Errore nell'esecuzione della query: {e}"

def handle_client(client_socket):
    """Gestisce la comunicazione con il client."""
    try:
        send_message(client_socket, "Collegamento riuscito, cosa vuoi fare?\n1. Scansioni\n2. Analisi DB")
        client_choice = client_socket.recv(1024).decode().strip()
        print(f"Scelta del client: {client_choice}")

        if client_choice == '1':
            print("Scelto scansioni")
            send_message(client_socket, "Hai scelto Scansioni. Su quale azienda vuoi fare la scansione?")
    
            dati_ricevuti = client_socket.recv(1024).decode().strip()
            if '|' in dati_ricevuti:  # Controlla se il delimitatore è presente
                azienda_choice, p_iva_choice = dati_ricevuti.split('|')
            else:
                azienda_choice, p_iva_choice = dati_ricevuti, "N/A"  # Caso di errore
    
            print(f"Azienda scelta per la scansione: {azienda_choice}, P.IVA: {p_iva_choice}")
            db_connection = create_db_connection()
            if db_connection:
                cursor = db_connection.cursor()
                query = """
                SELECT IP_sonda, Porta_sonda FROM aziende WHERE azienda = %s AND p_iva = %s
                """
                cursor.execute(query, (azienda_choice, p_iva_choice))
                result = cursor.fetchone()
            
            if result:
                ip_sonda = result[0]
                porta_sonda = result[1]
                try:
                    sonda_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                    sonda_socket.connect((ip_sonda, porta_sonda))
                    socket_conn = sonda_socket.recv(1024).decode()
                    print(f"{socket_conn}")
                    send_message(client_socket, f"Azienda trovata: {socket_conn}")
                    # Invia il messaggio di scansione al client
                    client_socket.send(
                        b"Che tipo di scansione vuoi fare?\n"
                        b"ARP_PASSIVA\n"
                        b"ARP_ATTIVA\n"
                        b"NMAP\n"
                        b"NBTSCAN\n"
                        b"ENUM4LINUX (solo dopo NBTSCAN)\n"
                        b"SMBMAP (solo dopo NBTSCAN)\n"
                        b"SMBCLIENT (solo dopo NBTSCAN)\n"
                        b"COMPLETA\n"
                    )
                    print("Messaggio di scansione inviato.")

                    try:
                        print("In attesa della scelta della scansione...")
                        scelta_scansione = client_socket.recv(1024).decode().strip()
                        if not scelta_scansione:  # Se non arriva una scelta valida, chiedi di nuovo
                            print("Nessuna scelta ricevuta, aspetto...")
                            send_message(client_socket, "Per favore, seleziona un tipo di scansione.")
                            scelta_scansione = client_socket.recv(1024).decode().strip()  # Riprova
                            print(f"Scelta scansione ricevuta dal client: {scelta_scansione}")
                            if not scelta_scansione:  # Ancora nulla? Gestisci errore
                                print("⚠️ Connessione interrotta dal client prima della scelta della scansione.")
                            else:
                                send_message(client_socket, f"Scansione {scelta_scansione} avviata.")
                        else:
                            send_message(client_socket, f"Scansione {scelta_scansione} avviata.")
                        
                    except Exception as e:
                        print(f"❌ Errore durante la ricezione della scelta: {e}")

                except Exception as e:
                    print(f"Errore nella connessione al server sonda: {e}")
                    send_message(client_socket, f"Errore nella connessione al server sonda: {e}")
            else:
                client_socket.send(b"Azienda non trovata")
        
        elif client_choice == '2':
            send_message(client_socket, f"Hai scelto Analisi DB.\nTabelle disponibili:\n1 tabella_host\n2.nbtscan\n3.smbclient\n4.nmap\n5.extended_enum\n6.smbmap\n7.scansioni\n8.masscan\nSeleziona una tabella (o usa '*' per tutte le colonne):")
            print("Scelto analisi DB")
            tabella = client_socket.recv(1024).decode().strip()
            print(f"tabella scelta:  {tabella}")
            client_socket.close()

    except Exception as e:
        print(f"Errore: {e}")


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
