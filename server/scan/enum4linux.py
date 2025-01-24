import subprocess
import json
import os
import mysql.connector

# Dati per la connessione al database MariaDB
DB_HOST = "localhost"  # Host del database
DB_NAME = "test"  # Nome del database
DB_USER = "root"  # Nome utente per il database
DB_PASS = "nuova_password"  # Password del database

# Funzione per connettersi al database
def connect_to_db():
    return mysql.connector.connect(
        host=DB_HOST,
        database=DB_NAME,
        user=DB_USER,
        password=DB_PASS,
        charset="utf8mb4",
        collation="utf8mb4_general_ci"
    )

# Funzione per eseguire enum4linux-ng e salvare i risultati nel database e nel file
def run_enum4linux(ip, output_file, connection):
    command = f"python3 enum4linux-ng/enum4linux-ng.py -A {ip} -oJ temp_output"
    subprocess.run(command, shell=True)

    # Verifica se il file JSON di output esiste
    json_file = "temp_output.json"  # Nome del file di output temporaneo
    if os.path.exists(json_file):
        with open(json_file, 'r') as f:
            data = json.load(f)  # Carica i dati JSON

        # Estrai i dati necessari per l'inserimento
        credentials_data = data.get("credentials", {})
        listeners_data = data.get("listeners", {})
        domain = data.get("domain", "")
        nmblookup = data.get("nmblookup", "")
        errors = data.get("errors", {})

        # Filtra i dati di credentials
        credentials = json.dumps({
            "auth_method": credentials_data.get("auth_method", "null"),
            "user": credentials_data.get("user", ""),
            "password": credentials_data.get("password", "")
        })

        # Filtra i listeners, mantenendo solo quelli accessibili (accessible: true)
        active_listeners = {}
        for listener, details in listeners_data.items():
            if details.get("accessible", False):  # Se accessible è True
                active_listeners[listener] = details
        listeners = json.dumps(active_listeners) if active_listeners else ""

        # Estrazione e salvataggio solo degli errori sotto "enum_listeners"
        enum_listeners_errors = errors.get("listeners", {}).get("enum_listeners", [])
        errors_str = json.dumps(enum_listeners_errors) if enum_listeners_errors else ""

        # Salva il domain normalmente
        domain_str = domain if domain else "null"  # Se domain è vuoto, salva "null"

        # Per nmblookup, se domain c'è, stampa "more info", altrimenti "null"
        nmblookup_str = "more info" if domain else "null"

        # Inserisci i dati nel database
        cursor = connection.cursor()
        insert_query = """
        INSERT INTO enum4linux (host, credentials, listeners, domain, nmblookup, errors)
        VALUES (%s, %s, %s, %s, %s, %s)
        """
        cursor.execute(insert_query, (ip, credentials, listeners, domain_str, nmblookup_str, errors_str))
        connection.commit()

        # Scrivi i dati nel file di output, aggiungendo nuovi risultati
        with open(output_file, 'a') as out_file:
            out_file.write(json.dumps(data, indent=4))  # Scrive i dati in formato leggibile
            out_file.write("\n---\n")  # Separa le voci con '---'

        # Rimuovi il file JSON temporaneo
        os.remove(json_file)

# Funzione principale
def main():
    output_file = "output_combined.json"  # Nome del file di output finale
    with open('nbtscan.txt', 'r') as file:
        lines = file.readlines()

    # Connetti al database
    connection = connect_to_db()

    # Itera su ogni linea e esegui enum4linux-ng per ogni IP
    for line in lines:
        # Splitta la linea usando '§' come delimitatore
        parts = line.split('§')
        if len(parts) > 0:
            ip_address = parts[0]  # L'indirizzo IP è nella prima colonna
            # Esegui il comando enum4linux-ng e salva i dati nel database
            run_enum4linux(ip_address, output_file, connection)

    # Chiudi la connessione al database
    connection.close()

if __name__ == "__main__":
    main()
