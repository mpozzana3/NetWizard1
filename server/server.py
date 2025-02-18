import socket
import subprocess
import mysql.connector
import re
import json
from datetime import datetime

# Leggere la configurazione dal file JSON
with open("config.json", "r") as config_file:
    config = json.load(config_file)

# Dati per la connessione al database MariaDB
DB_CONFIG = config["db"]
DB_HOST = DB_CONFIG["host"]
DB_NAME = DB_CONFIG["name"]
DB_USER = DB_CONFIG["user"]
DB_PASS = DB_CONFIG["password"]

# Configurazione del server socket
SERVER_CONFIG = config["server"]
HOST = SERVER_CONFIG["host"]
PORT = SERVER_CONFIG["port"]

# Dati dell'azienda
AZIENDA_CONFIG = config["azienda"]
P_IVA = AZIENDA_CONFIG["p_iva"]
AZIENDA = AZIENDA_CONFIG["nome"]

def subnet_extract():
    """Estrae la subnet dalla tabella di routing utilizzando il comando 'ip route'."""
    try:
        # Esegui il comando 'ip route'
        output = subprocess.check_output(["ip", "route"], text=True)
        
        # Cerca una riga con 'src' che contenga una subnet valida
        match = re.search(r"(\d+\.\d+\.\d+\.\d+/\d+)", output)
        if match:
            subnet = match.group(1)
            print(f"Subnet estratta: {subnet}")
            return subnet
        else:
            print("Nessuna subnet trovata nell'output.")
            return None
    except subprocess.CalledProcessError as e:
        print(f"Errore nell'esecuzione del comando 'ip route': {e}")
        return None
    except Exception as e:
        print(f"Errore generico: {e}")
        return None

def connect_db():
    """Crea una connessione al database MariaDB."""
    try:
        conn = mysql.connector.connect(
            host=DB_HOST,
            database=DB_NAME,
            user=DB_USER,
            password=DB_PASS,
            charset="utf8mb4",
            collation="utf8mb4_general_ci"
        )
        return conn
    except mysql.connector.Error as e:
        print(f"Errore nella connessione al database: {e}")
        return None

def create_stdout_if_not_exists():
    """Crea la tabella stdout se non esiste già."""
    conn = connect_db()
    if conn:
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS stdout (
                id_scansione INT PRIMARY KEY,
                stdout LONGTEXT,
                FOREIGN KEY (id_scansione) REFERENCES scansioni(id_scansione) ON DELETE CASCADE
            );
        """)
        conn.commit()
        cursor.close()
        conn.close()


def create_table_if_not_exists():
    """Crea la tabella scansioni se non esiste già."""
    conn = connect_db()
    if conn:
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS scansioni (
                id_scansione INT AUTO_INCREMENT PRIMARY KEY,
                p_iva VARCHAR(255) NOT NULL,
                timestamp TEXT,
                tipo_scansione VARCHAR(255) NOT NULL CHECK (tipo_scansione <> ''),
                stato INT NOT NULL,
                FOREIGN KEY (p_iva) REFERENCES aziende(p_iva) ON DELETE CASCADE
            );
        """)
        conn.commit()
        cursor.close()
        conn.close()

def insert_stdout(id_scansione, stdout):
    """Inserisce o aggiorna l'output della scansione nella tabella stdout."""
    conn = connect_db()
    if conn:
        cursor = conn.cursor()
        try:
            # Prova a fare un aggiornamento prima di un inserimento
            cursor.execute("""
                INSERT INTO stdout (id_scansione, stdout)
                VALUES (%s, %s)
                ON DUPLICATE KEY UPDATE stdout = CONCAT(stdout, %s)
            """, (id_scansione, stdout, stdout))
            conn.commit()
            print(f"Output della scansione con ID {id_scansione} aggiornato o inserito nella tabella stdout.")
        except mysql.connector.Error as e:
            print(f"Errore nell'inserimento o aggiornamento dell'output della scansione nel database: {e}")
        finally:
            cursor.close()
            conn.close()


def insert_scansioni(timestamp, tipo_scansione):
    """Inserisce i dati della scansione nella tabella scansioni e restituisce l'ID della scansione."""
    conn = connect_db()
    if conn:
        cursor = conn.cursor()
        try:
            cursor.execute("""
                INSERT INTO scansioni (p_iva, timestamp, tipo_scansione, stato)
                VALUES (%s, %s, %s, %s)
            """, (P_IVA, timestamp, tipo_scansione, 1))  # Stato "IN CORSO" = 1
            conn.commit()

            # Ottieni l'ID della scansione appena inserita
            id_scansione = cursor.lastrowid
            cursor.close()
            conn.close()
            return id_scansione
        except mysql.connector.Error as e:
            print(f"Errore nell'inserimento dei dati della scansione: {e}")
            cursor.close()
            conn.close()
            return None
    return None


def update_stato_scansione(id_scansione):
    """Aggiorna lo stato della scansione a COMPLETATA (0)."""
    conn = connect_db()
    if conn:
        cursor = conn.cursor()
        try:
            cursor.execute("""
                UPDATE scansioni
                SET stato = %s
                WHERE id_scansione = %s
            """, (0, id_scansione))  # Stato "COMPLETATA" = 0
            conn.commit()
            cursor.close()
            conn.close()
            print(f"Stato della scansione con ID {id_scansione} aggiornato a COMPLETATA.")
        except mysql.connector.Error as e:
            print(f"Errore nell'aggiornamento dello stato della scansione: {e}")
            cursor.close()
            conn.close()


def handle_client(client_socket, subnet):
    """Gestisce la comunicazione con il client."""
    while True:
        # Invia il messaggio di benvenuto
        client_socket.send(
            f"Collegamento riuscito. Ti sei collegato alla sonda dell'azienda {AZIENDA}.".encode()
        )

        # Ricevi la scelta di scansione dal client
        try:
            scelta_scansione = client_socket.recv(1024).decode().strip()
            print(f"Scelta scansione ricevuta: {scelta_scansione}")
            
            if scelta_scansione != "":
               timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            # Inserisci la scansione nel database
               id_scansione = insert_scansioni(timestamp, scelta_scansione)
            
            if id_scansione:
                print(f"Scelta scansione registrata nel database con ID: {id_scansione}")
                print(f"Lancio una scansione {scelta_scansione} con l'ID: {id_scansione}")
                client_socket.send(f"Lancio una scansione {scelta_scansione} con l'ID: {id_scansione}".encode())
            else:
                print(f"Errore nell'inserimento della scansione per {scelta_scansione}")
                client_socket.send(b"Errore nell'inserimento dei dati della scansione.\n")
                client_socket.close()
                print("Ho chiuso la connessione.")
                return  # Interrompi la connessione
        except Exception as e:
            print(f"Errore durante la ricezione della scelta: {e}")
            client_socket.send(b"Errore durante la ricezione della scelta di scansione.\n")
            client_socket.close()
            return  # Interrompi la connessione in caso di errore

        # Lancia il relativo script in base alla scelta
        try:
            if scelta_scansione == "ARP_PASSIVA":
                result = subprocess.run(["python3", "scan/scan-1.py", str(id_scansione)], capture_output=True, text=True, check=True)
                stdout = result.stdout 
            elif scelta_scansione == "ARP_ATTIVA":
                result = subprocess.run(["python3", "scan/scan-2.py", subnet, str(id_scansione)], capture_output=True, text=True, check=True)
                stdout = result.stdout                                    
            elif scelta_scansione == "NMAP": 
                result = subprocess.run(["python3", "scan/nmap.py", str(id_scansione), subnet], capture_output=True, text=True, check=True)
                stdout = result.stdout                                    
            elif scelta_scansione == "NBTSCAN":
                result = subprocess.run(["python3", "scan/NetBios.py", subnet, str(id_scansione)], capture_output=True, text=True, check=True)
                stdout = result.stdout 
            elif scelta_scansione == "ENUM4LINUX":
                result = subprocess.run(["python3", "scan/enum4linux.py", str(id_scansione)], capture_output=True, text=True, check=True)
                stdout = result.stdout                                    
            elif scelta_scansione == "SMBMAP":
                result = subprocess.run(["python3", "scan/smbmap.py", str(id_scansione)], capture_output=True, text=True, check=True)
                stdout = result.stdout                                    
            elif scelta_scansione == "SMBCLIENT":
                result = subprocess.run(["python3", "scan/smbclient.py", str(id_scansione)], capture_output=True, text=True, check=True)
                stdout = result.stdout                                    
            elif scelta_scansione == "COMPLETA":
                result = subprocess.run(["python3", "scan/main.py", str(id_scansione)], capture_output=True, text=True, check=True)
                stdout = result.stdout                                    
            elif scelta_scansione == "MASSCAN":
                result = subprocess.run(["python3", "scan/masscan.py", str(id_scansione)], capture_output=True, text=True, check=True)
                stdout = result.stdout                                    

            # Inserisci l'output nella tabella stdout
            insert_stdout(id_scansione, stdout)


            # Aggiorna lo stato della scansione a COMPLETATA
            update_stato_scansione(id_scansione)
            print(f"Scansione {scelta_scansione} terminata per l'ID {id_scansione}")
            client_socket.send(f"Scansione {scelta_scansione} terminata per l'ID {id_scansione}.\n".encode())

        except subprocess.CalledProcessError as e:
            print(f"Errore nell'esecuzione della scansione {scelta_scansione}: {e}")
            client_socket.send(f"Errore nell'esecuzione della scansione {scelta_scansione}.\n".encode())


                # Esegui lo script aggiornadb.py per aggiornare il database centrale con i valori del server sonda
        try:
            result2 = subprocess.run(["python3", "aggiornadb.py"], capture_output=True, text=True, check=True)
            if result2.stdout:
                 stdout2 = result2.stdout
            else:
                 stdout2 = "Nessun output prodotto dallo script."
    
            if result2.stderr:
                 stdout2 += "\n" + result2.stderr
            insert_stdout(id_scansione, stdout2)
            print("Script aggiornadb.py eseguito.")
            
            # Se lo script va a buon fine, invia un log al client
            client_socket.send(f"Script aggiornadb.py eseguito con successo. I dati sono stati aggiornati nel database centrale.\n".encode())
        except subprocess.CalledProcessError as e:
            print(f"Errore nell'esecuzione dello script aggiornadb.py: {e}")
            stdout2 = e.stderr if e.stderr else "Errore sconosciuto nell'esecuzione del comando."
            insert_stdout(id_scansione, stdout2)
            
            # Se lo script fallisce, invia un messaggio di errore al client
            client_socket.send(f"Errore nell'esecuzione dello script aggiornadb.py. Impossibile aggiornare il database centrale.\n".encode())
        
        # Chiudi la connessione
        client_socket.close()
        print("Ho chiuso la connessione.")
        break  # Esci dal ciclo while

def start_server():
    """Avvia il server per l'ascolto delle connessioni dei client."""
    create_table_if_not_exists()  # Crea la tabella nel DB se non esiste già
    create_stdout_if_not_exists()

    # Crea un socket TCP
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.bind((HOST, PORT))
    server_socket.listen(5)  # Può gestire fino a 5 connessioni simultanee

    print(f"Server in ascolto su {HOST}:{PORT}...")
    subnet = subnet_extract();
	

    while True:
        # Accetta una connessione in ingresso
        client_socket, client_address = server_socket.accept()
        print(f"Connessione ricevuta da {client_address}")

        # Gestisce la comunicazione con il client
        handle_client(client_socket, subnet)


if __name__ == "__main__":
    start_server()
