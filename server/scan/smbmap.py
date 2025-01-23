import csv
import os
import subprocess
import mysql.connector
from mysql.connector import Error
from datetime import datetime

def parse_nbtscan(file_path):
    """
    Legge il file nbtscan.txt ed estrae gli indirizzi IP.
    """
    ip_list = []
    with open(file_path, 'r') as f:
        lines = f.readlines()

    for line in lines:
        # Salta le righe che non contengono indirizzi IP
        if line.strip() and line[0].isdigit():
            ip = line.split()[0]  # Estrai il primo elemento della riga (IP address)
            ip_list.append(ip)
    
    return ip_list

def run_smbmap(ip_list, output_file):
    """
    Esegue smbmap per ogni IP e salva i risultati in un file CSV.
    """
    with open(output_file, 'w', newline='') as csvfile:
        csvwriter = csv.writer(csvfile)
        csvwriter.writerow(["IP", "Output"])  # Intestazione CSV

        for ip in ip_list:
            print(f"Eseguo smbmap per l'IP: {ip}")
            try:
                # Esegui il comando smbmap con sudo
                result = subprocess.run(
                    ["smbmap", "-H", ip, "--csv", "temp_smbmap.csv"],
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True
                )
                
                # Verifica se l'esecuzione è riuscita
                if result.returncode == 0:
                    # Leggi il file CSV temporaneo generato da smbmap
                    with open("temp_smbmap.csv", 'r') as temp_csv:
                        output = temp_csv.read()
                    
                    # Scrivi il risultato nel CSV finale
                    csvwriter.writerow([ip, output])
                else:
                    print(f"Errore con smbmap per l'IP {ip}: {result.stderr}")
                    csvwriter.writerow([ip, f"Errore: {result.stderr.strip()}"])
            except Exception as e:
                print(f"Errore durante l'esecuzione per l'IP {ip}: {e}")
                csvwriter.writerow([ip, f"Errore: {str(e)}"])

    # Rimuovi il file temporaneo se esiste
    if os.path.exists("temp_smbmap.csv"):
        os.remove("temp_smbmap.csv")

def connect_to_db():
    """
    Connessione al database MariaDB.
    """
    try:
        connection = mysql.connector.connect(
            host="localhost",
            user="root",  # Cambia con il tuo utente
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
        id INT AUTO_INCREMENT PRIMARY KEY,
        Host VARCHAR(255) NOT NULL,
        Share VARCHAR(255),
        Privs VARCHAR(255),
        Comment TEXT,
        timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """
    cursor = connection.cursor()
    cursor.execute(create_table_query)
    connection.commit()
    print("Tabella smbmap verificata o creata con successo.")

def insert_data_from_csv(connection, csv_file):
    """
    Inserisce i dati dal file smbmap.csv nella tabella smbmap.
    """
    with open(csv_file, 'r') as csvfile:
        csvreader = csv.reader(csvfile)
        next(csvreader)  # Salta l'intestazione
        
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
                            INSERT INTO smbmap (Host, Share, Privs, Comment, timestamp)
                            VALUES (%s, %s, %s, %s, %s);
                            """,
                            (host, share, privs, comment, timestamp)
                        )
        connection.commit()
    print("Dati inseriti nel database con successo.")

if __name__ == "__main__":
    input_file = "nbtscan.txt"
    output_file = "smbmap.csv"

    if not os.path.exists(input_file):
        print(f"Errore: Il file {input_file} non esiste.")
    else:
        # Estrai gli IP dal file
        ip_addresses = parse_nbtscan(input_file)
        print(f"Trovati {len(ip_addresses)} indirizzi IP.")

        # Esegui smbmap e salva i risultati
        run_smbmap(ip_addresses, output_file)
        print(f"Risultati salvati in {output_file}.")

        # Connessione al database e operazioni
        db_connection = connect_to_db()
        if db_connection:
            create_table_if_not_exists(db_connection)
            insert_data_from_csv(db_connection, output_file)
            db_connection.close()
