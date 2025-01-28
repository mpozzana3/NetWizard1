import mysql.connector
import logging

# Configurazione logging
logging.basicConfig(
    level=logging.INFO, 
    format='%(asctime)s - %(levelname)s - %(message)s'
)

try:
    # Connessione al primo database
    logging.info("Connessione al primo database...")
    conn1 = mysql.connector.connect(
        host="localhost",
        user="root",
        password="nuova_password",
        database="test",
        charset="utf8mb4",
        collation="utf8mb4_general_ci"
    )
    cursor1 = conn1.cursor()
    logging.info("Connessione al primo database completata.")

    # Connessione al secondo database
    logging.info("Connessione al secondo database...")
    conn2 = mysql.connector.connect(
        host="localhost",
        user="root",
        password="nuova_password",
        database="server_centrale",
        charset="utf8mb4",
        collation="utf8mb4_general_ci"
    )
    cursor2 = conn2.cursor()
    logging.info("Connessione al secondo database completata.")

    # Leggi i dati dal primo database
    logging.info("Lettura dati dalla tabella 'scansioni' del primo database...")
    cursor1.execute("SELECT * FROM scansioni")
    rows = cursor1.fetchall()
    logging.info(f"{len(rows)} record letti dalla tabella 'scansioni'.")

    # Inserisci i dati nel secondo database
    logging.info("Inserimento dati nel secondo database...")
    new_rows_count = 0  # Contatore per nuove righe inserite

    for row in rows:
        try:
            cursor2.execute(
                "INSERT INTO scansioni (id_scansione, p_iva, timestamp, tipo_scansione, stato) VALUES (%s, %s, %s, %s, %s)", 
                row
            )
            new_rows_count += 1  # Incrementa il contatore solo per nuove righe
            logging.info(f"Nuova riga inserita: {row}")
        except mysql.connector.Error as e:
            if e.errno == 1062:  # Codice errore per duplicato
                continue
            else:
                logging.error(f"Errore durante l'inserimento della riga {row}: {e}")
                raise  # Interrompi in caso di errori imprevisti

    # Log finale
    logging.info(f"Inserite {new_rows_count} nuove righe nel secondo database.")

    # Commit delle operazioni
    conn1.commit()
    conn2.commit()
    logging.info("Transazioni salvate con successo.")

except mysql.connector.Error as err:
    logging.error(f"Errore durante l'operazione: {err}")

finally:
    # Chiudi le connessioni
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
