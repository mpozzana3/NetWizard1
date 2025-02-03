import mysql.connector
import logging
import json

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
                raise

    logging.info(f"Inserite {new_rows_count} nuove righe in 'scansioni'.")

    # Trasferimento dati dalla tabella tabella_host
    logging.info("Lettura dati dalla tabella 'tabella_host'...")
    cursor1.execute("SELECT * FROM tabella_host")
    rows = cursor1.fetchall()
    logging.info(f"{len(rows)} record letti dalla tabella 'tabella_host'.")

    logging.info("Inserimento dati in 'tabella_host' nel secondo database...")
    new_rows_count = 0

    for row in rows:
        row_with_piva = row + (azienda_config['p_iva'],)
        try:
            cursor2.execute(
                "INSERT INTO tabella_host (id_scansione, ip, mac_address, time_stamp, vendor, tipo_scansione, p_iva) VALUES (%s, %s, %s, %s, %s, %s, %s)",
                row_with_piva
            )
            new_rows_count += 1
        except mysql.connector.Error as e:
            if e.errno == 1062:
                continue
            else:
                logging.error(f"Errore durante l'inserimento della riga {row}: {e}")
                raise

    logging.info(f"Inserite {new_rows_count} nuove righe in 'tabella_host'.")

    # Trasferimento dati dalla tabella nmap
    logging.info("Lettura dati dalla tabella 'nmap'...")
    cursor1.execute("SELECT * FROM nmap")
    rows = cursor1.fetchall()
    logging.info(f"{len(rows)} record letti dalla tabella 'nmap'.")

    logging.info("Inserimento dati in 'nmap' nel secondo database...")
    new_rows_count = 0

    for row in rows:
        row_with_piva = row + (azienda_config['p_iva'],)
        try:
            cursor2.execute(
                "INSERT INTO nmap (id_scansione, ip, timestamp, vendor, hostname, extraports_count, extraports_state, port_id, port_script_id, port_state, port_script_output, port_service_name, p_iva) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)",
                row_with_piva
            )
            new_rows_count += 1
        except mysql.connector.Error as e:
            if e.errno == 1062:
                continue
            else:
                logging.error(f"Errore durante l'inserimento della riga {row}: {e}")
                raise

    logging.info(f"Inserite {new_rows_count} nuove righe in 'nmap'.")
	
	# Trasferimento dati dalla tabella nbtscan
    logging.info("Lettura dati dalla tabella 'nbtscan'...")
    cursor1.execute("SELECT * FROM nbtscan")
    rows = cursor1.fetchall()
    logging.info(f"{len(rows)} record letti dalla tabella 'nbtscan'.")

    logging.info("Inserimento dati in 'nbtscan' nel secondo database...")
    new_rows_count = 0

    for row in rows:
        row_with_piva = row + (azienda_config['p_iva'],)
        try:
            cursor2.execute(
                "INSERT INTO nbtscan (id_scansione, ip, netbios_name, server, user, mac_address, timestamp, p_iva) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)",
                row_with_piva
            )
            new_rows_count += 1
        except mysql.connector.Error as e:
            if e.errno == 1062:
                continue
            else:
                logging.error(f"Errore durante l'inserimento della riga {row}: {e}")
                raise

    logging.info(f"Inserite {new_rows_count} nuove righe in 'nbtscan'.")

        # Trasferimento dati dalla tabella enum4linux
    logging.info("Lettura dati dalla tabella 'enum4linux'...")
    cursor1.execute("SELECT * FROM enum4linux")
    rows = cursor1.fetchall()
    logging.info(f"{len(rows)} record letti dalla tabella 'enum4linux'.")

    logging.info("Inserimento dati in 'enum4linux' nel secondo database...")
    new_rows_count = 0

    for row in rows:
        row_with_piva = row + (azienda_config['p_iva'],)
        try:
            cursor2.execute(
                "INSERT INTO enum4linux (id_scansione, ip, credentials, listeners, domain, nmblookup, errors, timestamp, p_iva) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)",
                row_with_piva
            )
            new_rows_count += 1
        except mysql.connector.Error as e:
            if e.errno == 1062:
                continue
            else:
                logging.error(f"Errore durante l'inserimento della riga {row}: {e}")
                raise

    logging.info(f"Inserite {new_rows_count} nuove righe in 'enum4linux'.")

    # Trasferimento dati dalla tabella smbclient
    logging.info("Lettura dati dalla tabella 'smbclient'...")
    cursor1.execute("SELECT * FROM smbclient")
    rows = cursor1.fetchall()
    logging.info(f"{len(rows)} record letti dalla tabella 'smbclient'.")

    logging.info("Inserimento dati in 'smbclient' nel secondo database...")
    new_rows_count = 0

    for row in rows:
        row_with_piva = row + (azienda_config['p_iva'],)
        try:
            cursor2.execute(
                "INSERT INTO smbclient (id_scansione, ip, login_anonimo, p_iva) VALUES (%s, %s, %s, %s)",
                row_with_piva
            )
            new_rows_count += 1
        except mysql.connector.Error as e:
            if e.errno == 1062:
                continue
            else:
                logging.error(f"Errore durante l'inserimento della riga {row}: {e}")
                raise

    logging.info(f"Inserite {new_rows_count} nuove righe in 'smbclient'.")

    # Trasferimento dati dalla tabella smbmap
    logging.info("Lettura dati dalla tabella 'smbmap'...")
    cursor1.execute("SELECT * FROM smbmap")
    rows = cursor1.fetchall()
    logging.info(f"{len(rows)} record letti dalla tabella 'smbmap'.")

    logging.info("Inserimento dati in 'smbmap' nel secondo database...")
    new_rows_count = 0

    for row in rows:
        row_with_piva = row + (azienda_config['p_iva'],)
        try:
            cursor2.execute(
                "INSERT INTO smbmap (id_scansione, ip, Share, Privs, Comment, timestamp, p_iva) VALUES (%s, %s, %s, %s, %s, %s, %s)",
                row_with_piva
            )
            new_rows_count += 1
        except mysql.connector.Error as e:
            if e.errno == 1062:
                continue
            else:
                logging.error(f"Errore durante l'inserimento della riga {row}: {e}")
                raise

    logging.info(f"Inserite {new_rows_count} nuove righe in 'smbmap'.")

    # Trasferimento dati dalla tabella extended_enum
    logging.info("Lettura dati dalla tabella 'extended_enum'...")
    cursor1.execute("SELECT * FROM extended_enum")
    rows = cursor1.fetchall()
    logging.info(f"{len(rows)} record letti dalla tabella 'extended_enum'.")

    logging.info("Inserimento dati in 'extended_enum' nel secondo database...")
    new_rows_count = 0

    for row in rows:
        row_with_piva = row + (azienda_config['p_iva'],)
        try:
            cursor2.execute(
                "INSERT INTO extended_enum (id_scansione, ip, json_data, timestamp, p_iva) VALUES (%s, %s, %s, %s, %s)",
                row_with_piva
            )
            new_rows_count += 1
        except mysql.connector.Error as e:
            if e.errno == 1062:
                continue
            else:
                logging.error(f"Errore durante l'inserimento della riga {row}: {e}")
                raise

    logging.info(f"Inserite {new_rows_count} nuove righe in 'extended_enum'.")

   # Trasferimento dati dalla tabella masscan
    logging.info("Lettura dati dalla tabella 'masscan'...")
    cursor1.execute("SELECT * FROM masscan")
    rows = cursor1.fetchall()
    logging.info(f"{len(rows)} record letti dalla tabella 'masscan'.")
    logging.info("Inserimento dati in 'masscan' nel secondo database...")
    new_rows_count = 0

    for row in rows:
        row_with_piva = row + (azienda_config['p_iva'],)
        try:
            cursor2.execute(
                "INSERT INTO masscan (id_scansione, ip, addrtype, port_protocol, portid, state, reason, reason_ttl, timestamp, p_iva) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)",
                row_with_piva
            )
            new_rows_count += 1
        except mysql.connector.Error as e:
            if e.errno == 1062:
                continue
            else:
                logging.error(f"Errore durante l'inserimento della riga {row}: {e}")
                raise

    logging.info(f"Inserite {new_rows_count} nuove righe in 'masscan'.")


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
