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
            CREATE TABLE IF NOT EXISTS aziende (
                id INT AUTO_INCREMENT PRIMARY KEY,
                azienda VARCHAR(255) NOT NULL,
                p_iva VARCHAR(255) NOT NULL UNIQUE
            );
        """)
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

def insert_aziende(azienda, p_iva):
    """Inserisce i dati azienda e P.IVA nel database se non esistono già."""
    conn = connect_db()
    if conn:
        cursor = conn.cursor()
        try:
            # Tentativo di inserimento diretto
            cursor.execute("INSERT INTO aziende (azienda, p_iva) VALUES (%s, %s)", (azienda, p_iva))
            conn.commit()
            cursor.close()
            conn.close()
            return "INSERTED"
        except mysql.connector.IntegrityError as e:
            # Controlla se l'errore è dovuto a una chiave duplicata
            if "Duplicate entry" in str(e):
                # Recupera il nome associato alla p_iva
                cursor.execute("SELECT azienda FROM aziende WHERE p_iva = %s", (p_iva,))
                result = cursor.fetchone()
                cursor.close()
                conn.close()

                if result and result[0] == azienda:
                    return "EXISTS_SAME"
                else:
                    return "EXISTS_DIFFERENT"
            else:
                cursor.close()
                conn.close()
                return "ERROR"
        except mysql.connector.Error as e:
            print(f"Errore nell'inserimento dei dati: {e}")
            cursor.close()
            conn.close()
            return "ERROR"
    return "ERROR"

def insert_scansioni(p_iva, tipo_scansione):
    """Inserisce i dati della scansione nella tabella scansioni."""
    conn = connect_db()
    if conn:
        cursor = conn.cursor()
        try:
            cursor.execute("""
                INSERT INTO scansioni (p_iva, tipo_scansione, stato)
                VALUES (%s, %s, %s)
            """, (p_iva, tipo_scansione, 1))  # Stato "IN CORSO" = 1
            conn.commit()
            cursor.close()
            conn.close()
            return True
        except mysql.connector.Error as e:
            print(f"Errore nell'inserimento dei dati della scansione: {e}")
            cursor.close()
            conn.close()
            return False
    return False

def handle_client(client_socket):
    """Gestisce la comunicazione con il client."""
    while True:
        # Invia il messaggio di benvenuto
        client_socket.send(b"Collegamento riuscito.\nInserisci il nome dell'azienda e la P.IVA.\n")

        # Ricevi il nome dell'azienda e la P.IVA dal client
        azienda = client_socket.recv(1024).decode().strip()
        p_iva = client_socket.recv(1024).decode().strip()

        # Debug: stampa i valori ricevuti
        print(f"Azienda: {azienda}, P.IVA: {p_iva}")
        
        # Inserisci i dati nel database
        if azienda and p_iva:
            result = insert_aziende(azienda, p_iva)
            if result == "INSERTED":
                client_socket.send(f"Dati ricevuti e inseriti correttamente. Procedo con la scansione.\n".encode())
                break  # Dati corretti, esci dal ciclo
            elif result == "EXISTS_SAME":
                client_socket.send(f"La P.IVA è già associata. Procedo con la scansione.\n".encode())
                break  # Dati corretti, esci dal ciclo
            elif result == "EXISTS_DIFFERENT":
                client_socket.send(f"Errore: La P.IVA {p_iva} esiste già ma con un nome azienda diverso. Riprova.\n".encode())
            else:
                client_socket.send(b"Errore nell'inserimento dei dati. Riprova.\n")
        else:
            client_socket.send(b"Dati azienda o P.IVA mancanti. Riprova.\n")

    # Solo se i dati sono corretti, il server chiede il tipo di scansione
    while True:
        # Invia il messaggio di scansione al client
        client_socket.send(b"Che tipo di scansione vuoi fare?\n1. ARP_PASSIVA\n2. ARP_ATTIVA\n3. NMAP\n4. COMPLETA\n")
        print("Messaggio di scansione inviato.")

        # Ricevi la scelta di scansione dal client
        scelta_scansione = client_socket.recv(1024).decode().strip()
        print(f"Scelta scansione ricevuta dal client: {scelta_scansione}")

        # Inserisci la scansione nel database
        if insert_scansioni(p_iva, scelta_scansione):
            client_socket.send(b"Scansione registrata nel database.\n")
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
