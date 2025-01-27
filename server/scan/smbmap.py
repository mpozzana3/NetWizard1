import csv
import os
import subprocess
import mysql.connector
from mysql.connector import Error
from datetime import datetime

def parse_nbtscan(file_path):
    """
    Legge il file nbtscan.txt ed estrae gli indirizzi IP dal nuovo formato.
    """
    ip_list = []
    with open(file_path, 'r') as f:
        lines = f.readlines()

    for line in lines:
        if line.strip():
            parts = line.split('§')
            if len(parts) > 0:
                ip = parts[0]
                ip_list.append(ip)

    return ip_list

def run_smbmap(ip_list, output_file):
    """
    Esegue smbmap per ogni IP e salva i risultati in un file CSV.
    """
    with open(output_file, 'w', newline='') as csvfile:
        csvwriter = csv.writer(csvfile)
        csvwriter.writerow(["IP", "Output"])

        for ip in ip_list:
            print(f"Eseguo smbmap per l'IP: {ip}")
            try:
                result = subprocess.run(
                    ["smbmap", "-H", ip, "--csv", "temp_smbmap.csv"],
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True
                )
                if result.returncode == 0:
                    with open("temp_smbmap.csv", 'r') as temp_csv:
                        output = temp_csv.read()
                    csvwriter.writerow([ip, output])
                else:
                    print(f"Errore con smbmap per l'IP {ip}: {result.stderr}")
                    csvwriter.writerow([ip, f"Errore: {result.stderr.strip()}"])
            except Exception as e:
                print(f"Errore durante l'esecuzione per l'IP {ip}: {e}")
                csvwriter.writerow([ip, f"Errore: {str(e)}"])

    if os.path.exists("temp_smbmap.csv"):
        os.remove("temp_smbmap.csv")

def connect_to_db():
    """
    Connessione al database MariaDB.
    """
    try:
        connection = mysql.connector.connect(
            host="localhost",
            user="root",
            password="nuova_password",
            database="test",
            charset="utf8mb4",
            collation="utf8mb4_general_ci"
        )
        if connection.is_connected():
            print("Connessione al database MariaDB riuscita!")
        return connection
    except Error as e:
        print(f"Errore durante la connessione a MariaDB: {e}")
        return None

def create_table_if_not_exists(connection):
    """
    Crea la tabella smbmap se non esiste.
    """
    create_table_query = """
    CREATE TABLE IF NOT EXISTS smbmap (
        id_scansione INT NOT NULL,
        Host VARCHAR(255) NOT NULL,
        Share VARCHAR(255),
        Privs VARCHAR(255),
        Comment TEXT,
        timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        PRIMARY KEY (id_scansione, Host, Share)
    );
    """
    cursor = connection.cursor()
    cursor.execute(create_table_query)
    connection.commit()
    print("Tabella smbmap verificata o creata con successo.")

def insert_data_from_csv(connection, csv_file, id_scansione):
    """
    Inserisce i dati dal file smbmap.csv nella tabella smbmap.
    """
    with open(csv_file, 'r') as csvfile:
        csvreader = csv.reader(csvfile)
        next(csvreader)

        cursor = connection.cursor()
        for row in csvreader:
            ip, output = row
            lines = output.splitlines()
            for line in lines:
                if line and not line.startswith("Host,Share,Privs,Comment"):
                    data = line.split(",")
                    if len(data) == 4:
                        host, share, privs, comment = data
                        timestamp = datetime.now()
                        cursor.execute(
                            """
                            INSERT INTO smbmap (id_scansione, Host, Share, Privs, Comment, timestamp)
                            VALUES (%s, %s, %s, %s, %s, %s);
                            """,
                            (id_scansione, host, share, privs, comment, timestamp)
                        )
        connection.commit()
    print("Dati inseriti nel database con successo.")

if __name__ == "__main__":
    import sys
    if len(sys.argv) != 2:
        print("Uso: python3 smbmap.py <id_scansione>")
        sys.exit(1)

    id_scansione = int(sys.argv[1])  # Legge l'argomento id_scansione
    input_file = "nbtscan.txt"
    output_file = "smbmap.csv"

    if not os.path.exists(input_file):
        print(f"Errore: Il file {input_file} non esiste.")
    else:
        ip_addresses = parse_nbtscan(input_file)
        print(f"Trovati {len(ip_addresses)} indirizzi IP.")

        run_smbmap(ip_addresses, output_file)
        print(f"Risultati salvati in {output_file}.")

        db_connection = connect_to_db()
        if db_connection:
            create_table_if_not_exists(db_connection)
            insert_data_from_csv(db_connection, output_file, id_scansione)
            db_connection.close()

