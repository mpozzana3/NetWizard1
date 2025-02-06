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
PORT = config['server']['port']

# Parametri DB MariaDB
DB_HOST = config['database']['db_host']
DB_USER = config['database']['db_user']
DB_PASSWORD = config['database']['db_password']
DB_NAME = config['database']['db_name']

def handle_exit_signal(signal, frame):
    print("\nServer chiuso.")
    sys.exit(0)

signal.signal(signal.SIGINT, handle_exit_signal)  

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
    """Lancia mariadbquery.py con una query e restituisce il risultato."""
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
        client_choice = client_socket.recv(1024).decode()
        print(f"Scelta del client: {client_choice}")

        #Se viene scelto Scansioni
        if client_choice == '1':
            send_message(client_socket, "Hai scelto Scansioni. Su quale azienda vuoi fare la scansione?")
            azienda_choice = client_socket.recv(1024).decode()
            p_iva_choice = client_socket.recv(1024).decode()
            print(f"Azienda scelta per la scansione: {azienda_choice}, P.IVA: {p_iva_choice}")

            #si collega al DB e controlla se l'azienda è presente in DB e p_iva corrisponde, se si estrae i valori per connettersi al server sonda
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

                    # Connessione al server sonda
                    try:
                        sonda_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                        sonda_socket.connect((ip_sonda, porta_sonda))
                        socket_conn = sonda_socket.recv(1024).decode()
                        print(f"{socket_conn}")

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

                        # Ricevi la scelta di scansione dal client
                        try:
                            scelta_scansione = client_socket.recv(1024).decode().strip()
                        except Exception as e:
                            print(f"Errore durante la ricezione della scelta: {e}")
                            client_socket.send(b"Errore: Scelta di scansione non ricevuta. Connessione chiusa.\n")
                            scelta_scansione = None

                        # Controlla se la connessione si è interrotta
                        if not scelta_scansione:
                            print("Connessione interrotta dal client prima della scelta della scansione.")
                            client_socket.close()
                            return  

                        print(f"Scelta scansione ricevuta dal client: {scelta_scansione}")

                        # Verifica se la scelta è valida
                        scansioni_valide = [
                            "ARP_PASSIVA", "ARP_ATTIVA", "NMAP", "NBTSCAN", "ENUM4LINUX", "SMBMAP", "SMBCLIENT", "COMPLETA"
                        ]

                        if scelta_scansione not in scansioni_valide:
                            print(f"Scelta scansione non valida: {scelta_scansione}")
                            client_socket.send(b"Errore: Scelta di scansione non valida. Connessione chiusa.\n")
                            client_socket.close()
                            print("Ho chiuso la connessione per scelta non valida.")
                            return  

                        # Invia il comando di scansione al server sonda
                        client_socket.send(b"Scelta di scansione valida. Richiesta inviata al server-sonda.\n")
                        sonda_socket.sendall(scelta_scansione.encode())
                        print(f"Comando di scansione inviato al server sonda: {scelta_scansione}")

                        # Ricevi la risposta dal server sonda
                        risposta_sonda = sonda_socket.recv(1024).decode()
                        print(f"Risposta dal server sonda: {risposta_sonda}")
                        send_message(client_socket, f"Risposta dal server sonda: {risposta_sonda}")

                        # Ricevi la risposta dal server sonda
                        risposta_sonda = sonda_socket.recv(1024).decode()
                        print(f"Risposta dal server sonda: {risposta_sonda}")
                        send_message(client_socket, f"{risposta_sonda}")
                        client_socket.close()

                        # Chiudi la connessione con il server sonda
                        sonda_socket.close()

                    except Exception as e:
                        print(f"Errore nella connessione al server sonda: {e}")
                        send_message(client_socket, f"Errore nella connessione al server sonda: {e}")
                else:
                    send_message(client_socket, "Azienda non trovata o non valida.")
                    client_socket.close()
                
                cursor.close()
                db_connection.close()

        #Se viene scelto AnalisiDB
        elif client_choice == '2':
            try:
                # Manda le tabelle al client
                send_message(client_socket, f"Hai scelto Analisi DB.\nTabelle disponibili:\n1 tabella_host\n2.nbtscan\n3.smbclient\n4.nmap\n5.extended_enum\n6.smbmap\n7.scansioni\n8.masscan\n")

                # Ricevi la tabella scelta dal client
                tab = client_socket.recv(1024).decode().strip()
                print(f"Tabella scelta dal client: {tab}")

                # Ottieni l'elenco delle colonne della tabella scelta
                columns_query = f"SELECT COLUMN_NAME FROM information_schema.columns WHERE table_schema = 'server_centrale' AND table_name = '{tab}'"
                columns_result = execute_query(columns_query)

                # Manda la lista delle colonne presenti in tabella al client
                send_message(client_socket, f"Colonne della tabella '{tab}':\n{columns_result}\nUsa '*' per tutte le colonne o seleziona specifiche colonne.")

                # Ricevi la selezione delle colonne (o '*' per tutte le colonne)
                col = client_socket.recv(1024).decode().strip()
                print(f"Colonne selezionate dal client: {col}")

                # Ora invia un messaggio per chiedere se desidera un vincolo opzionale
                send_message(client_socket, f"Se vuoi applicare un vincolo (opzionale) su una colonna, indicamelo ora. Ad esempio, 'colonna = 'valore'', altrimenti 'NO'.")

                # Ricevi il vincolo opzionale dal client
                vincolo = client_socket.recv(1024).decode().strip()
                print(f"Vincolo ricevuto dal client: {vincolo}")

                # Costruisci la parte WHERE della query 
                if vincolo == 'NO':
                    where_clause = ""
                else:
                    where_clause = f" WHERE {vincolo}"

                # Costruisci la query completa
                complete_query = f"SELECT {col} FROM {tab}{where_clause}"
                print(f"Eseguo la query: {complete_query}")
                # Esegui la query del client
                result = execute_query(complete_query)
                send_message(client_socket, result)
                print(f"Risultato: {result}")

            except Exception as e:
                send_message(client_socket, f"Errore: {e}")

            finally:
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
