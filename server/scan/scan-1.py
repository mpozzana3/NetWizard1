import mysql.connector
from scapy.all import ARP, sniff
import json
from macaddress import get_mac_vendor
import sys
from datetime import datetime
import random
from mac_vendor_lookup import MacLookup

# Leggere la configurazione dal file JSON
with open("config.json", "r") as config_file:
    config = json.load(config_file)

# Dati per la connessione al database MariaDB
DB_CONFIG = config["db"]
DB_HOST = DB_CONFIG["host"]
DB_NAME = DB_CONFIG["name"]
DB_USER = DB_CONFIG["user"]
DB_PASS = DB_CONFIG["password"]

output_file = "test.txt"

# Carica i dati dei vendor dal file JSON
def load_vendor_data(json_file):
    """Carica i dati dei vendor dal file JSON."""
    try:
        with open(json_file, 'r') as file:
            vendor_data = json.load(file)
        return vendor_data
    except Exception as e:
        print(f"Errore nel caricamento del file JSON: {e}")
        return None

# Connessione al database MariaDB
def connect_db():
    try:
        conn = mysql.connector.connect(
            host=DB_HOST,
            database=DB_NAME,
            user=DB_USER,
            password=DB_PASS,
            charset="utf8mb4",
            collation="utf8mb4_general_ci"
        )
        return conn
    except mysql.connector.Error as e:
        print(f"Errore nella connessione al database: {e}")
        return None

def load_vendor_data(json_file):
    """Carica i dati dei vendor dal file JSON."""
    try:
        with open(json_file, 'r') as file:
            vendor_data = json.load(file)
        return vendor_data
    except Exception as e:
        print(f"Errore nel caricamento del file JSON: {e}")
        return None

# Funzione per creare la tabella se non esiste
def create_table(conn):
    """Crea la tabella per memorizzare i dati ARP se non esiste."""
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS tabella_host (
            id_scansione VARCHAR(255),
            ip VARCHAR(15),
            mac_address VARCHAR(17),
            timestamp TEXT,
            vendor VARCHAR(255),
            tipo_scansione VARCHAR(255) DEFAULT NULL,
            PRIMARY KEY (id_scansione, mac_address)
        );
    """)
    conn.commit()
    cursor.close()

def insert_into_db(conn, id_scansione, ip, mac, timestamp, vendor, tipo_scansione="ARP_PASSIVO"):
    """Inserisce i dati ARP nella tabella del database solo se la coppia id_scansione e mac_address non esistono."""
    cursor = conn.cursor()
    try:
        cursor.execute("""
            INSERT INTO tabella_host (id_scansione, ip, mac_address, timestamp, vendor, tipo_scansione)
            VALUES (%s, %s, %s, %s, %s, %s);
        """, (id_scansione, ip, mac, timestamp, vendor, tipo_scansione))
        conn.commit()
        print(f"IP: {ip} - MAC: {mac} - Vendor: {vendor} inserito nel database.")
    except mysql.connector.Error as e:
        print(f"Errore nell'inserimento: {e}")
    cursor.close()

def process_packet(packet, vendor_data, id_scansione):
    """Elabora i pacchetti ARP per individuare dispositivi attivi e salvarli nel file e nel database."""
    if ARP in packet and packet[ARP].op in (1, 2):  # ARP request (1) o reply (2)
        mac = packet[ARP].hwsrc
        ip = packet[ARP].psrc
        timestamp = packet.time  # Timestamp del pacchetto
        # Recupera il vendor del MAC usando la funzione dal modulo macaddress.py
        mac_vendor = get_mac_vendor(mac, vendor_data)

        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        # Salva nel file
        with open(output_file, "a") as f:
            f.write(f"IP: {ip} - MAC: {mac} - Vendor: {vendor} - {timestamp}\n")

        print(f"IP: {ip}, MAC: {mac}, Vendor: {mac_vendor}")

        # Connessione al database e inserimento dati
        conn = connect_db()
        if conn:
            insert_data(conn, id_scansione, ip, mac, timestamp, mac_vendor, "arp-passivo")
            conn.close()

# Funzione principale
def main():
    # Verifica che l'ID della scansione sia stato passato come argomento
    if len(sys.argv) < 2:
        print("Errore: è necessario fornire l'ID della scansione come argomento.")
        return
    
    # Prendi l'ID della scansione dalla riga di comando
    id_scansione = sys.argv[1]

    # Carica i dati del vendor dal file JSON
    vendor_data = load_vendor_data('mac-vendors-export.json')

    if not vendor_data:
        print("Impossibile caricare i dati del vendor. Termino.")
        return

    # Genera un id_scansione casuale
    id_scansione = random.randint(100000, 999999)

    # Connessione al database e creazione della tabella se non esiste
    conn = connect_db()
    if conn:
        create_table_if_not_exists(conn)
        conn.close()

    print(f"Inizio scansione ARP. ID scansione: {id_scansione}. Premere Ctrl+C per interrompere.")
    try:
        # Avvia lo sniffing sulla rete per pacchetti ARP
        sniff(filter="arp", prn=lambda packet: process_packet(packet, vendor_data, id_scansione), store=False, timeout=200)
    except KeyboardInterrupt:
        print("\nScansione interrotta dall'utente.")

if __name__ == "__main__":
    main()
