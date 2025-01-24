import socket
import subprocess
import datetime
import mysql.connector

# Dati per la connessione al database MariaDB
DB_HOST = "localhost"
DB_NAME = "test"
DB_USER = "root"
DB_PASS = "nuova_password"

# Configurazione del server socket
HOST = "0.0.0.0"  # Ascolta su tutte le interfacce di rete
PORT = 5003  # Porta per la comunicazione
P_IVA = "IT12345679810"
AZIENDA = "GFTECH"

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

def create_table_if_not_exists():
    """Crea la tabella se non esiste già."""
    conn = connect_db()
    if conn:
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS scansioni (
                id_scansione INT AUTO_INCREMENT PRIMARY KEY,
                p_iva VARCHAR(255) NOT NULL,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                tipo_scansione VARCHAR(255) NOT NULL,
                stato INT NOT NULL,
	  	FOREIGN KEY (p_iva) REFERENCES aziende(p_iva) ON DELETE CASCADE
            );
        """)
        conn.commit()
        cursor.close()
        conn.close()


import subprocess

def insert_scansioni(tipo_scansione):
    """Inserisce i dati della scansione nella tabella scansioni e restituisce l'ID della scansione."""
    conn = connect_db()
    if conn:
        cursor = conn.cursor()
        try:
            cursor.execute("""
                INSERT INTO scansioni (p_iva, tipo_scansione, stato)
                VALUES (%s, %s, %s)
            """, (P_IVA, tipo_scansione, 1))  # Stato "IN CORSO" = 1
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

def handle_client(client_socket):
    """Gestisce la comunicazione con il client."""
    while True:
        # Invia il messaggio di benvenuto
        client_socket.send(
            f"Collegamento riuscito.\nTi sei collegato alla sonda dell'azienda {AZIENDA}.\n".encode()
        )

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
        scelta_scansione = client_socket.recv(1024).decode().strip()
        print(f"Scelta scansione ricevuta dal client: {scelta_scansione}")

        # Inserisci la scansione nel database e ottieni l'ID della scansione
        id_scansione = insert_scansioni(scelta_scansione)
        if id_scansione:
            client_socket.send(b"Scansione registrata nel database.\n")
            print(f"Scelta scansione registrata nel database con ID: {id_scansione}")

            # Lancia il relativo script in base alla scelta
            try:
                if scelta_scansione == "ARP_PASSIVA":
                    subprocess.run(["python3", "scan/scan-1.py", str(id_scansione)], check=True)
                    print(f"Scansione ARP_PASSIVA avviata per l'ID {id_scansione}")

                elif scelta_scansione == "ARP_ATTIVA":
                    subprocess.run(["python3", "scan/scan-2.py", "172.16.1.0/24", str(id_scansione)], check=True)
                    print(f"Scansione ARP_ATTIVA avviata per l'ID {id_scansione}")

                elif scelta_scansione == "NMAP":
                    subprocess.run(["python3", "scan/nmap.py", str(id_scansione)], check=True)
                    print(f"Scansione NMAP avviata per l'ID {id_scansione}")

                elif scelta_scansione == "NBTSCAN":
                    subprocess.run(["python3", "scan/NetBios.py", "172.16.1.0/24", str(id_scansione)], check=True)
                    print(f"Scansione NBTSCAN avviata per l'ID {id_scansione}")

                elif scelta_scansione == "ENUM4LINUX":
                    subprocess.run(["python3", "scan/enum4linux.py", str(id_scansione)], check=True)
                    print(f"Scansione ENUM4LINUX avviata per l'ID {id_scansione}")

                elif scelta_scansione == "SMBMAP":
                    subprocess.run(["python3", "scan/smbmap.py", str(id_scansione)], check=True)
                    print(f"Scansione SMBMAP avviata per l'ID {id_scansione}")

                elif scelta_scansione == "SMBCLIENT":
                    subprocess.run(["python3", "scan/smbclient.py", str(id_scansione)], check=True)
                    print(f"Scansione SMBCLIENT avviata per l'ID {id_scansione}")

                elif scelta_scansione == "COMPLETA":
                    subprocess.run(["python3", "scan/main.py", str(id_scansione)], check=True)
                    print(f"Scansione COMPLETA avviata per l'ID {id_scansione}")

            except subprocess.CalledProcessError as e:
                print(f"Errore nell'esecuzione della scansione {scelta_scansione}: {e}")
                client_socket.send(f"Errore nell'esecuzione della scansione {scelta_scansione}.\n".encode())
        else:
            client_socket.send(b"Errore nell'inserimento dei dati della scansione.\n")

        # Chiudi la connessione
        client_socket.close()
        print("Ho chiuso la connessione.")
        break
 
def start_server():
    """Avvia il server per l'ascolto delle connessioni dei client."""
    create_table_if_not_exists()  # Crea la tabella nel DB se non esiste già

    # Crea un socket TCP
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.bind((HOST, PORT))
    server_socket.listen(5)  # Può gestire fino a 5 connessioni simultanee

    print(f"Server in ascolto su {HOST}:{PORT}...")

    while True:
        # Accetta una connessione in ingresso
        client_socket, client_address = server_socket.accept()
        print(f"Connessione ricevuta da {client_address}")

        # Gestisce la comunicazione con il client
        handle_client(client_socket)

if __name__ == "__main__":
    start_server()
