import mysql.connector
import logging
import json
import sys

# Carica il file di configurazione
with open('config.json', 'r') as f:
    config = json.load(f)

# Estrai le informazioni dalla configurazione
db_config = config['db']
server_config = config['server']
azienda_config = config['azienda']

# Configurazione logging
logging.basicConfig(
    level=logging.INFO, 
    format='%(asctime)s - %(levelname)s - %(message)s'
)

check = True  # Variabile di controllo

try:
    # Connessione al primo database
    logging.info("Connessione al primo database...")
    conn1 = mysql.connector.connect(
        host=db_config['host'],
        user=db_config['user'],
        password=db_config['password'],
        database=db_config['name'],
        charset="utf8mb4",
        collation="utf8mb4_general_ci"
    )
    cursor1 = conn1.cursor()
    logging.info("Connessione al primo database completata.")

    # Connessione al secondo database
    logging.info("Connessione al secondo database...")
    conn2 = mysql.connector.connect(
        host=db_config['host'],
        user=db_config['user'],
        password=db_config['password'],
        database="server_centrale",
        charset="utf8mb4",
        collation="utf8mb4_general_ci"
    )
    cursor2 = conn2.cursor()
    logging.info("Connessione al secondo database completata.")

    # Trasferimento dati dalla tabella scansioni
    logging.info("Lettura dati dalla tabella 'scansioni'...")
    cursor1.execute("SELECT * FROM scansioni")
    rows = cursor1.fetchall()
    logging.info(f"{len(rows)} record letti dalla tabella 'scansioni'.")

    logging.info("Inserimento dati in 'scansioni' nel secondo database...")
    new_rows_count = 0

    for row in rows:
        try:
            cursor2.execute(
                "INSERT INTO scansioni (id_scansione, p_iva, timestamp, tipo_scansione, stato) VALUES (%s, %s, %s, %s, %s)",
                row
            )
            new_rows_count += 1
        except mysql.connector.Error as e:
            if e.errno == 1062:
                continue
            else:
                logging.error(f"Errore durante l'inserimento della riga {row}: {e}")
                check = False  # Segna errore critico
                raise

    logging.info(f"Inserite {new_rows_count} nuove righe in 'scansioni'.")


    # Funzione di inserimento dei dati in una tabella
    def insert_data_to_db(cursor, table, query, rows):
        new_rows_count = 0
        for row in rows:
            try:
                cursor.execute(query, row)
                new_rows_count += 1
            except mysql.connector.Error as e:
                if e.errno == 1062:  # Ignora duplicati
                    continue
                else:
                    logging.error(f"Errore durante l'inserimento della riga {row} nella tabella {table}: {e}")
                    global check
                    check = False  # Segna errore critico
                    raise  # Rilancia l'eccezione per interrompere...
        logging.info(f"Inserite {new_rows_count} nuove righe in '{table}'.")

    # Lista delle tabelle con le query di inserimento e le relative letture
    tables = [
        ("tabella_host", "SELECT * FROM tabella_host", 
         "INSERT INTO tabella_host (id_scansione, ip, mac_address, timestamp, vendor, tipo_scansione, p_iva) VALUES (%s, %s, %s, %s, %s, %s, %s)"),
        ("nmap", "SELECT * FROM nmap", 
         "INSERT INTO nmap (id_scansione, ip, timestamp, vendor, hostname, extraports_count, extraports_state, port_id, port_state, port_service_name, port_product, port_script_id, port_script_output, p_iva) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)"),
        ("nbtscan", "SELECT * FROM nbtscan", 
         "INSERT INTO nbtscan (id_scansione, ip, netbios_name, server, user, mac_address, timestamp, p_iva) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)"),
        ("enum4linux", "SELECT * FROM enum4linux", 
         "INSERT INTO enum4linux (id_scansione, ip, credentials, listeners, domain, nmblookup, errors, timestamp, p_iva) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)"),
        ("smbclient", "SELECT * FROM smbclient", 
         "INSERT INTO smbclient (id_scansione, ip, login_anonimo, timestamp, p_iva) VALUES (%s, %s, %s,  %s, %s)"),
        ("smbmap", "SELECT * FROM smbmap", 
         "INSERT INTO smbmap (id_scansione, ip, Share, Privs, Comment, timestamp, p_iva) VALUES (%s, %s, %s, %s, %s, %s, %s)"),
        ("file_scansioni", "SELECT * FROM file_scansioni", 
         "INSERT INTO file_scansioni (id_scansione, nmapxml, enum4json, masscanxml, nmaphtml, p_iva) VALUES (%s, %s, %s, %s, %s, %s)"),
        ("extended_enum", "SELECT * FROM extended_enum", 
         "INSERT INTO extended_enum (id_scansione, ip, json_data, timestamp, p_iva) VALUES (%s, %s, %s, %s, %s)"),
        ("masscan", "SELECT * FROM masscan", 
         "INSERT INTO masscan (id_scansione, ip, addrtype, port_protocol, portid, state, reason, reason_ttl, timestamp, p_iva) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)")
    ]

    # Ciclo sulle tabelle
    for table, select_query, insert_query in tables:
        logging.info(f"Lettura dati dalla tabella '{table}'...")
        cursor1.execute(select_query)
        rows = cursor1.fetchall()
        logging.info(f"{len(rows)} record letti dalla tabella '{table}'.")

        # Aggiungi p_iva a ciascun record
        rows_with_piva = [row + (azienda_config['p_iva'],) for row in rows]

        # Inserisci i dati nel secondo database
        logging.info(f"Inserimento dati in '{table}' nel secondo database...")
        insert_data_to_db(cursor2, table, insert_query, rows_with_piva)

    # Commit delle operazioni
    conn1.commit()
    conn2.commit()
    logging.info("Transazioni salvate con successo.")

except mysql.connector.Error as err:
    logging.error(f"Errore durante l'operazione: {err}")

finally:
    if 'cursor1' in locals():
        cursor1.close()
    if 'conn1' in locals():
        conn1.close()
        logging.info("Connessione al primo database chiusa.")
    if 'cursor2' in locals():
        cursor2.close()
    if 'conn2' in locals():
        conn2.close()
        logging.info("Connessione al secondo database chiusa.")
if not check:
    logging.error("L'operazione è stata interrotta a causa di un errore critico.")
    sys.exit(1)
