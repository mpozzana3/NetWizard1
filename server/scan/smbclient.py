import subprocess
import re
import mysql.connector
import argparse
import json


# Leggere la configurazione dal file JSON
with open("config.json", "r") as config_file:
    config = json.load(config_file)

# Dati per la connessione al database MariaDB
DB_CONFIG = config["db"]
DB_HOST = DB_CONFIG["host"]
DB_NAME = DB_CONFIG["name"]
DB_USER = DB_CONFIG["user"]
DB_PASS = DB_CONFIG["password"]

def connect_to_db():
    """
    Connessione a MariaDB.
    """
    return mysql.connector.connect(
        host=DB_HOST,
        database=DB_NAME,
        user=DB_USER,
        password=DB_PASS,
        charset="utf8mb4",
        collation="utf8mb4_general_ci"
    )

def create_table_if_not_exists(connection):
    """
    Crea la tabella 'smbclient' se non esiste.
    """
    query = """
    CREATE TABLE IF NOT EXISTS smbclient (
        id_scansione VARCHAR(255) NOT NULL,
        ip VARCHAR(15) NOT NULL,
        login_anonimo VARCHAR(20) NOT NULL,
        PRIMARY KEY (id_scansione, ip)
    )
    """
    cursor = connection.cursor()
    cursor.execute(query)
    connection.commit()

def parse_nbtscan(file_path):
    """
    Legge il file nbtscan.txt ed estrae gli indirizzi IP.
    """
    ip_list = []
    with open(file_path, 'r') as f:
        lines = f.readlines()

    for line in lines:
        # Salta le righe vuote e quelle che non contengono indirizzi IP
        if line.strip():
            # Splitta la riga usando il delimitatore '§'
            parts = line.split('§')
            if len(parts) > 0:
                ip = parts[0]  # L'indirizzo IP è nella prima colonna
                ip_list.append(ip)
    return ip_list

def run_smbclient_scan(ip):
    """
    Esegue il comando smbclient -L su un IP e restituisce l'output.
    """
    try:
        result = subprocess.run(['smbclient', '-L', f'\\\\{ip}', '-N'], capture_output=True, text=True, timeout=60)
        if result.returncode == 0:
            return result.stdout
        else:
            return f"Errore sconosciuto per {ip}: {result.stderr.strip()}"
    except subprocess.TimeoutExpired:
        return f"Errore sconosciuto per {ip}: timed out after 60 seconds"
    except Exception as e:
        return f"Errore sconosciuto per {ip}: {str(e)}"

def parse_scan_output(ip, output):
    """
    Analizza l'output della scansione e determina lo stato del login anonimo.
    """
    if "Anonymous login successful" in output:
        return "success"
    elif "session setup failed" in output or "Errore sconosciuto" in output:
        return "failure"
    else:
        return "unknown"

def save_results_to_db(results, connection, id_scansione):
    """
    Salva i risultati nel database, includendo l'id_scansione.
    """
    cursor = connection.cursor()
    insert_query = """
    INSERT INTO smbclient (id_scansione, ip, login_anonimo) VALUES (%s, %s, %s)
    """
    for ip, login_anonimo in results.items():
        cursor.execute(insert_query, (id_scansione, ip, login_anonimo))
    connection.commit()

def main(input_file, id_scansione):
    """
    Funzione principale che esegue la scansione SMB e salva i risultati nel database.
    """
    # Connetti al database
    connection = connect_to_db()
    create_table_if_not_exists(connection)

    ips = parse_nbtscan(input_file)
    results = {}
    for ip in ips:
        print(f"Scansionando {ip}...")
        output = run_smbclient_scan(ip)
        login_anonimo = parse_scan_output(ip, output)
        results[ip] = login_anonimo
        print(f"Risultato per {ip}: {login_anonimo}")

    save_results_to_db(results, connection, id_scansione)
    print("Scansione completata. I risultati sono stati salvati nel database.")

    # Chiudi la connessione al database
    connection.close()

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Esegui la scansione SMB e salva i risultati nel database")
    parser.add_argument("id_scansione", help="ID della scansione da inserire nel database")
    args = parser.parse_args()

    input_file = 'nbtscan.txt'

    # Esegui lo script con gli argomenti passati
    main(input_file, args.id_scansione)
