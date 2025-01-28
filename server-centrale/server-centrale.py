import socket
import mysql.connector
import subprocess
import signal
import sys

# Parametri del server
HOST = '127.0.0.1'  # Indirizzo IP del server (localhost per test)
PORT = 12345         # Porta di connessione

# Parametri DB MariaDB
DB_HOST = 'localhost'
DB_USER = 'root'
DB_PASSWORD = 'nuova_password'
DB_NAME = 'server_centrale'

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
        if connection.is_connected():
            print("Connessione al database riuscita!")
            return connection
    except mysql.connector.Error as e:
        print(f"Errore nella connessione al database: {e}")
        return None

def handle_client(client_socket):
    """Gestisce la comunicazione con il client."""
    try:
        # Invia il messaggio di benvenuto al client
        welcome_message = "Collegamento riuscito, cosa vuoi fare?\n1. Scansioni\n2. Analisi DB"
        client_socket.send(welcome_message.encode())

        # Ricevi la risposta dal client
        client_choice = client_socket.recv(1024).decode()
        print(f"Scelta del client: {client_choice}")

        # In base alla scelta del client, esegui un'azione
        if client_choice == '1':
            response = "Hai scelto Scansioni. Su quale azienda vuoi fare la scansione?"
            client_socket.send(response.encode())

            # Ricevi il nome dell'azienda e la P.IVA dal client
            azienda_choice = client_socket.recv(1024).decode()
            p_iva_choice = client_socket.recv(1024).decode()
            print(f"Azienda scelta per la scansione: {azienda_choice}, P.IVA: {p_iva_choice}")

            # Connessione al database
            db_connection = create_db_connection()
            if db_connection:
                cursor = db_connection.cursor()

                # Esegui la query per cercare l'azienda nel database
                query = """
                SELECT IP_sonda, Porta_sonda
                FROM aziende
                WHERE azienda = %s AND p_iva = %s
                """
                cursor.execute(query, (azienda_choice, p_iva_choice))

                # Recupera i risultati della query
                result = cursor.fetchone()

                if result:
                    ip_sonda, porta_sonda = result
                    response = f"IP della sonda: {ip_sonda}, Porta della sonda: {porta_sonda}"
                else:
                    response = "Azienda non ancora inserita in DB."

                # Invia la risposta al client
                client_socket.send(response.encode())
                cursor.close()
                db_connection.close()

        elif client_choice == '2':
            response = "Hai scelto Analisi DB. Inserisci una query SQL."
            client_socket.send(response.encode())

            # Ricevi la query dal client
            query = client_socket.recv(1024).decode()
            print(f"Query ricevuta dal client: {query}")

            if query.strip().lower() == 'exit':
                print("Chiusura connessione.")
                client_socket.send("Connessione chiusa.".encode())
                return

            # Esegui il file mariadbquery.py con la query ricevuta
            try:
                result = subprocess.run(["python3", "mariadbquery.py", query], capture_output=True, text=True, check=True)
                client_socket.send(result.stdout.encode())  # Invia l'output della query al client
            except subprocess.CalledProcessError as e:
                print(f"Errore nell'esecuzione del sottoprocesso: {e}")
                client_socket.send("Errore nell'esecuzione della query.".encode())

        else:
            response = "Scelta non valida."
            client_socket.send(response.encode())

    except Exception as e:
        print(f"Errore nella gestione del client: {e}")
        client_socket.send("Errore durante la comunicazione.".encode())
    finally:
        client_socket.close()

def start_server():
    """Avvia il server e accoglie le connessioni."""
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.bind((HOST, PORT))
    server_socket.listen(5)
    print(f"Server in ascolto su {HOST}:{PORT}...")

    while True:
        # Accetta una connessione da un client
        client_socket, client_address = server_socket.accept()
        print(f"Connessione stabilita con {client_address}")

        # Gestisci la comunicazione con il client
        handle_client(client_socket)

if __name__ == "__main__":
    start_server()

