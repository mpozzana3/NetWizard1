import subprocess
import json
import os
import mysql.connector
import argparse

# Leggere la configurazione dal file JSON
with open("config.json", "r") as config_file:
    config = json.load(config_file)

# Dati per la connessione al database MariaDB
DB_CONFIG = config["db"]
DB_HOST = DB_CONFIG["host"]
DB_NAME = DB_CONFIG["name"]
DB_USER = DB_CONFIG["user"]
DB_PASS = DB_CONFIG["password"]

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

# Funzione per creare la tabella enum4linux se non esiste
def create_enum4linux_table(connection):
    cursor = connection.cursor()
    create_table_query = """
    CREATE TABLE IF NOT EXISTS enum4linux (
        id_scansione VARCHAR(255) NOT NULL,
        ip VARCHAR(15),
        credentials TEXT,
        listeners TEXT,
        domain TEXT,
        nmblookup TEXT,
        errors TEXT,
        timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        PRIMARY KEY (id_scansione, ip)
    );
    """
    cursor.execute(create_table_query)
    connection.commit()
    cursor.close()

# Funzione per creare la tabella extended_enum se non esiste
def create_extended_enum_table(connection):
    cursor = connection.cursor()
    create_table_query = """
    CREATE TABLE IF NOT EXISTS extended_enum (
        id_scansione VARCHAR(255) NOT NULL,
        ip VARCHAR(15) NOT NULL,
        json_data TEXT,
        timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        PRIMARY KEY (id_scansione, ip)
    );
    """
    cursor.execute(create_table_query)
    connection.commit()
    cursor.close()

# Funzione per inserire dati nella tabella extended_enum
def insert_into_extended_enum(connection, id_scansione, ip, json_data):
    cursor = connection.cursor()
    insert_query = """
    INSERT INTO extended_enum (id_scansione, ip, json_data)
    VALUES (%s, %s, %s)
    """
    cursor.execute(insert_query, (id_scansione, ip, json_data))
    connection.commit()
    cursor.close()

# Funzione per eseguire enum4linux-ng e salvare i risultati nel database e nel file
def run_enum4linux(ip, output_file, connection, id_scansione):
    command = f"python3 scan/enum4linux-ng/enum4linux-ng.py -A {ip} -oJ temp_output"
    subprocess.run(command, shell=True)

    json_file = "temp_output.json"
    if os.path.exists(json_file):
        with open(json_file, 'r') as f:
            data = json.load(f)

        credentials_data = data.get("credentials", {})
        listeners_data = data.get("listeners", {})
        domain = data.get("domain", "")
        nmblookup = data.get("nmblookup", "null")
        errors = data.get("errors", {})

        credentials = json.dumps({
            "auth_method": credentials_data.get("auth_method", "null"),
            "user": credentials_data.get("user", ""),
            "password": credentials_data.get("password", "")
        })

        active_listeners = {k: v for k, v in listeners_data.items() if v.get("accessible", False)}
        listeners = json.dumps(active_listeners) if active_listeners else ""
        errors_str = json.dumps(errors.get("listeners", {}).get("enum_listeners", [])) if errors.get("listeners", {}).get("enum_listeners", []) else ""
        domain_str = domain if domain else "null"
        nmblookup_str = "more info" if domain else "null"

        cursor = connection.cursor()
        insert_query = """
        INSERT INTO enum4linux (id_scansione, ip, credentials, listeners, domain, nmblookup, errors)
        VALUES (%s, %s, %s, %s, %s, %s, %s)
        """
        cursor.execute(insert_query, (id_scansione, ip, credentials, listeners, domain_str, nmblookup_str, errors_str))
        connection.commit()
        cursor.close()

        with open(output_file, 'a') as out_file:
            out_file.write(json.dumps(data, indent=4))
            out_file.write("\n---\n")

        # se nmblookup diverso da null, è ricco di informazioni, allora inseriamo in un'altra tabella tutto il file json
        if nmblookup != "null":
            insert_into_extended_enum(connection, id_scansione, ip, json.dumps(data))

        os.remove(json_file)

# Funzione principale
def main():
    parser = argparse.ArgumentParser(description="Esegui una scansione Enum4Linux e inserisci i dati nel database MariaDB.")
    parser.add_argument("id_scansione", help="ID della scansione da associare ai dati.")
    args = parser.parse_args()

    output_file = "output_combined.json"
    with open('nbtscan.txt', 'r') as file:
        lines = file.readlines()

    connection = connect_to_db()
    create_enum4linux_table(connection)
    create_extended_enum_table(connection)

    for line in lines:
        parts = line.split('§')
        if len(parts) > 0:
            ip_address = parts[0]
            run_enum4linux(ip_address, output_file, connection, args.id_scansione)

    connection.close()

if __name__ == "__main__":
    main()
