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
        client_choice = client_socket.recv(1024).decode()
        print(f"Scelta del client: {client_choice}")


        if client_choice == '1':
            send_message(client_socket, "Hai scelto Scansioni. Su quale azienda vuoi fare la scansione?")
            azienda_choice = client_socket.recv(1024).decode()
            p_iva_choice = client_socket.recv(1024).decode()
            print(f"Azienda scelta per la scansione: {azienda_choice}, P.IVA: {p_iva_choice}")

            db_connection = create_db_connection()
            if db_connection:
                cursor = db_connection.cursor()
                query = """
                SELECT IP_sonda, Porta_sonda FROM aziende WHERE azienda = %s AND p_iva = %s
                """
                cursor.execute(query, (azienda_choice, p_iva_choice))
                result = cursor.fetchone()
                response = f"IP della sonda: {result[0]}, Porta della sonda: {result[1]}" if result else "Azienda non ancora inserita in DB."
                send_message(client_socket, response)
                cursor.close()
                db_connection.close()
        
        elif client_choice == '2':
            send_message(client_socket, "Hai scelto Analisi DB. Inserisci una query SQL.")
            query = client_socket.recv(1024).decode()
            print(f"Query ricevuta dal client: {query}")


            if query.strip().lower() == 'exit':
                send_message(client_socket, "Connessione chiusa.")
                return

            result = execute_query(query)
            send_message(client_socket, result)
        
        else:
            send_message(client_socket, "Scelta non valida.")
    
    except Exception as e:
        send_message(client_socket, f"Errore: {e}")
    
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
