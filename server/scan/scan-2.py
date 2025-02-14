import sys
import mysql.connector
from scapy.all import ARP, Ether, srp
import json
from macaddress import get_mac_vendor
from datetime import datetime

# Leggere la configurazione dal file JSON
with open("config.json", "r") as config_file:
    config = json.load(config_file)

# Dati per la connessione al database MariaDB
DB_CONFIG = config["db"]
DB_HOST = DB_CONFIG["host"]
DB_NAME = DB_CONFIG["name"]
DB_USER = DB_CONFIG["user"]
DB_PASS = DB_CONFIG["password"]

def load_vendor_data(json_file):
    try:
        with open(json_file, 'r') as file:
            vendor_data = json.load(file)
        return vendor_data
    except Exception as e:
        print(f"Errore nel caricamento del file JSON: {e}")
        return None

def connect_db():
    try:
        conn = mysql.connector.connect(
            host=DB_HOST,
            database=DB_NAME,
            user=DB_USER,
            password=DB_PASS,
            charset="utf8mb4",  # Specifica un charset compatibile
            collation="utf8mb4_general_ci"  # Aggiunge la collation compatibile per la connessione
        )
        return conn
    except Exception as e:
        print(f"Errore nella connessione al database: {e}")
        return None

def create_table(conn):
    with conn.cursor() as cursor:
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

def insert_into_db(conn, ip, mac, timestamp, vendor, id_scansione, tipo_scansione="ARP_ATTIVO"):
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

def arp_scan(target_ip_range, vendor_data, id_scansione):
    arp_request = ARP(pdst=target_ip_range)
    broadcast = Ether(dst="ff:ff:ff:ff:ff:ff")
    arp_request_broadcast = broadcast/arp_request
    
    print(f"Scansione ARP in corso su {target_ip_range}...")
    answered_list = srp(arp_request_broadcast, timeout=10, verbose=False)[0]
    
    devices = []
        
    for element in answered_list:
        ip = element[1].psrc
        mac = element[1].hwsrc
        vendor = get_mac_vendor(mac, vendor_data)
        print(f"IP: {ip} - MAC: {mac} - Vendor: {vendor}")
        
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        with open("test_attività.txt", "a") as f:   
            f.write(f"IP: {ip} - MAC: {mac} - Vendor: {vendor} - {timestamp}\n")

        conn = connect_db()
        if conn:
            insert_into_db(conn, ip, mac, timestamp, vendor, id_scansione)
            conn.close()
            
        devices.append((ip, mac, vendor))
            
    return devices

# Funzione principale che esegue la scansione ARP
def run_scan_directly(target_ip_range, id_scansione):
    vendor_data = load_vendor_data('mac-vendors-export.json')
    if not vendor_data:
        print("Impossibile caricare i dati del vendor")
        return

    conn = connect_db()
    if conn:
        create_table(conn)
        conn.close()

    devices = arp_scan(target_ip_range, vendor_data, id_scansione)

    if not devices:
        print("Nessun dispositivo trovato")
    else:
        print(f"{len(devices)} dispositivi trovati")

if __name__ == "__main__":
    if len(sys.argv) > 2:
        target_ip_range = sys.argv[1]
        id_scansione = sys.argv[2]
        run_scan_directly(target_ip_range, id_scansione)
    else:
        print("Per favore, fornisci un intervallo IP e un ID scansione come argomenti.")
