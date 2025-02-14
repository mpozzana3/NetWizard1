import subprocess
import mysql.connector
from mysql.connector import Error
import argparse
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

# Funzione per connettersi al database e creare la tabella se non esiste
def connect_to_db():
    try:
        connection = mysql.connector.connect(
            host=DB_HOST,
            database=DB_NAME,
            user=DB_USER,
            password=DB_PASS,
            charset="utf8mb4",
            collation="utf8mb4_general_ci"
        )
        if connection.is_connected():
            print("Connessione al database riuscita.")
            cursor = connection.cursor()
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS nbtscan (
                    id_scansione VARCHAR(255),
                    ip VARCHAR(15) NOT NULL,
                    netbios_name VARCHAR(255),
                    server VARCHAR(255),
                    user VARCHAR(255),
                    mac_address VARCHAR(17),
                    timestamp TEXT,
                    PRIMARY KEY (id_scansione, ip)
                );
            """)
            connection.commit()
            return connection, cursor
    except Error as e:
        print(f"Errore durante la connessione al database: {e}")
        return None, None

# Funzione per inserire i dati nel database
def insert_data(cursor, id_scansione, ip_address, netbios_name, server, user, mac_address, timestamp):
    try:
        cursor.execute("""
            INSERT INTO nbtscan (id_scansione, ip, netbios_name, server, user, mac_address, timestamp)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
        """, (id_scansione, ip_address, netbios_name, server, user, mac_address, timestamp))
    except Error as e:
        print(f"Errore durante l'inserimento dei dati: {e}")

# Funzione per eseguire nbtscan e processare i risultati
def run_nbtscan(ip_range, id_scansione):
    print("Inizio scansione...")

    # Esegui il comando nbtscan
    command = f"nbtscan -s § {ip_range} | tee nbtscan.txt"
    process = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

    # Leggi l'output e processa i risultati
    output, error = process.communicate()
    if process.returncode != 0:
        print(f"Errore nell'esecuzione di nbtscan: {error.decode()}")
        return

    print("Fine scansione.")

    # Splitta l'output in righe e ignora eventuali righe vuote
    lines = output.decode().strip().split("\n")
    results = [line.split("§") for line in lines if line.strip()]

    # Connessione al database
    connection, cursor = connect_to_db()
    if not connection:
        return

    # Inserisci i dati nel database
    for result in results:
        # Completa la lista con stringhe vuote se necessario
        result = [field.strip() for field in result]
        while len(result) < 5:
            result.append("<unknown>")

        ip_address = result[0]
        netbios_name = result[1] if result[1] else "<unknown>"
        server = result[2] if result[2] else "<unknown>"
        user = result[3] if result[3] else "<unknown>"
        mac_address = result[4] if result[4] else "<unknown>"
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        # Inserisci i dati
        insert_data(cursor, id_scansione, ip_address, netbios_name, server, user, mac_address, timestamp)

    # Commit e chiusura della connessione
    connection.commit()
    cursor.close()
    connection.close()


if __name__ == "__main__":
    # Parsing degli argomenti dalla riga di comando
    parser = argparse.ArgumentParser(description="Esegui una scansione NetBios e inserisci i dati nel database MariaDB.")
    parser.add_argument("ip_range", help="Il range IP da scansionare.")
    parser.add_argument("id_scansione", help="ID della scansione da associare ai dati.")
    args = parser.parse_args()

    # Esegui la scansione con l'IP range e l'ID scansione forniti
    run_nbtscan(args.ip_range, args.id_scansione)
