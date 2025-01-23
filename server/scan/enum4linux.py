import subprocess
import os
import re
import mysql.connector
from datetime import datetime

# Dati per la connessione al database MariaDB
DB_HOST = "localhost"
DB_NAME = "test"
DB_USER = "root"
DB_PASS = "nuova_password"

NBTSCAN_FILE = "nbtscan.txt"
ENUM_OUTPUT_FILE = "enum4linux.txt"

def extract_ips(file_path):
    """
    Legge il file nbtscan.txt e restituisce una lista di indirizzi IP.
    """
    ips = []
    try:
        with open(file_path, "r") as file:
            for line in file:
                match = re.match(r"(\d+\.\d+\.\d+\.\d+)", line)
                if match:
                    ips.append(match.group(1))
    except FileNotFoundError:
        print(f"Errore: Il file {file_path} non esiste nella directory.")
    return ips

def run_enum4linux(ip):
    """
    Esegue il comando `enum4linux -Sd <ip>` e scrive l'output in un file.
    """
    try:
        command = ["enum4linux", "-S", ip]
        with open(ENUM_OUTPUT_FILE, "a") as output_file:
            output_file.write(f"\n\n--- Scansione per {ip} ---\n")
            subprocess.run(command, stdout=output_file, stderr=subprocess.STDOUT, text=True)
            print(f"Scansione completata per {ip}")
    except Exception as e:
        print(f"Errore durante la scansione di {ip}: {e}")


def parse_enum4linux_output(file_path):
    results = []
    current_scan = None

    try:
        with open(file_path, "r") as file:
            for line in file:
                line = line.strip()

                # Rileva l'inizio di una nuova scansione
                if line.startswith("--- Scansione per"):
                    if current_scan:  # Salva la scansione precedente
                        results.append(current_scan)
                    current_scan = {
                        "IP": None,
                        "Domain": "Unknown",  # Default value
                        "Vulnerable": "NO",
                        "Timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    }

                # Estrai l'IP
                ip_match = re.search(r"Target\s+\.+\s+(\d+\.\d+\.\d+\.\d+)", line)
                if ip_match and current_scan:
                    current_scan["IP"] = ip_match.group(1)

                # Estrai il dominio
                domain_match = re.search(r"\[\+\] Got domain/workgroup name: (\S+)", line)
                if domain_match and current_scan:
                    current_scan["Domain"] = domain_match.group(1)

                # Determina vulnerabilità
                if "[+] Server" in line and "allows sessions using username '', password ''" in line:
                    if current_scan:
                        current_scan["Vulnerable"] = "YES"

            # Aggiungi l'ultima scansione se presente
            if current_scan:
                results.append(current_scan)

        print(f"Dati estratti dall'output: {results}")
    except FileNotFoundError:
        print(f"Errore: Il file {file_path} non esiste.")
    except Exception as e:
        print(f"Errore durante il parsing: {e}")

    return results

def create_and_populate_table(data):
    try:
        conn = mysql.connector.connect(
            host=DB_HOST, database=DB_NAME, user=DB_USER, password=DB_PASS, charset="utf8mb4", collation="utf8mb4_general_ci"
        )
        cursor = conn.cursor()

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS enum4linux (
                id INT AUTO_INCREMENT PRIMARY KEY,
                ip VARCHAR(15) NOT NULL,
                timestamp DATETIME NOT NULL,
                domain VARCHAR(255) NOT NULL,
                vulnerable ENUM('YES', 'NO') NOT NULL
            )
        """)
        conn.commit()

        print("Dati da inserire (prima della conversione in tuple):", data)

        # Controlla che tutti i dizionari abbiano le chiavi richieste
        for entry in data:
            if "Domain" not in entry:
                print(f"Errore: Mancano informazioni sul dominio per {entry.get('IP', 'Indirizzo sconosciuto')}")
                entry["Domain"] = "Unknown"

        # Converti i dizionari in tuple
        tuple_data = [(d["IP"], d["Timestamp"], d["Domain"], d["Vulnerable"]) for d in data]

        print("Dati convertiti in tuple:", tuple_data)

        # Inserisci i dati nel database
        insert_query = """
            INSERT INTO enum4linux (ip, timestamp, domain, vulnerable)
            VALUES (%s, %s, %s, %s)
        """
        cursor.executemany(insert_query, tuple_data)
        conn.commit()

        print(f"Tabella enum4linux aggiornata con {len(data)} record.")
    except mysql.connector.Error as err:
        print(f"Errore durante la connessione al database: {err}")
    finally:
        if conn.is_connected():
            cursor.close()
            conn.close()

def main():
    print("Inizio scansione...")
    ips = extract_ips(NBTSCAN_FILE)
    if not ips:
        print("Nessun indirizzo IP trovato.")
        return

    # Rimuove il file di output se già esiste
    if os.path.exists(ENUM_OUTPUT_FILE):
        os.remove(ENUM_OUTPUT_FILE)

    for ip in ips:
        run_enum4linux(ip)

    print("Scansione completata. Analisi dell'output...")
    scan_results = parse_enum4linux_output(ENUM_OUTPUT_FILE)
    if not scan_results:
        print("Nessun dato estratto dall'output.")
        return

    print("Connessione al database e aggiornamento della tabella...")
    create_and_populate_table(scan_results)

if __name__ == "__main__":
    main()

