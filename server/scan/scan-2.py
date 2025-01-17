import sys
import psycopg2
from scapy.all import ARP, Ether, srp
import json
from macaddress import get_mac_vendor
from flask import Flask, request, jsonify

# Dati per la connessione al database PostgreSQL
DB_HOST = "localhost"
DB_NAME = "tirocinio"
DB_USER = "postgres"
DB_PASS = "20134"

app = Flask(__name__)

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
        conn = psycopg2.connect(
            host=DB_HOST,
            dbname=DB_NAME,
            user=DB_USER,
            password=DB_PASS
        )
        return conn
    except Exception as e:
        print(f"Errore nella connessione al database: {e}")
        return None

def create_table(conn):
    with conn.cursor() as cursor:
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS arp_data (
                id SERIAL PRIMARY KEY,
                ip VARCHAR(15) UNIQUE,
                mac VARCHAR(17),
                vendor VARCHAR(255),
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """)
        conn.commit()

def insert_into_db(conn, ip, mac, vendor):
    with conn.cursor() as cursor:
        cursor.execute("""
            INSERT INTO arp_data (ip, mac, vendor) VALUES (%s, %s, %s)
            ON CONFLICT (ip) DO NOTHING;
        """, (ip, mac, vendor))
        conn.commit()

def arp_scan(target_ip_range, vendor_data):
    arp_request = ARP(pdst=target_ip_range)
    broadcast = Ether(dst="ff:ff:ff:ff:ff:ff")
    arp_request_broadcast = broadcast/arp_request
    
    print(f"Scansione ARP in corso su {target_ip_range}...")
    answered_list = srp(arp_request_broadcast, timeout=2, verbose=False)[0]
    
    devices = []
        
    for element in answered_list:
        ip = element[1].psrc
        mac = element[1].hwsrc
        vendor = get_mac_vendor(mac, vendor_data)
        print(f"IP: {ip} - MAC: {mac} - Vendor: {vendor}")
        
        with open("test_attività.txt", "a") as f:   
            f.write(f"IP: {ip} - MAC: {mac} - Vendor: {vendor}\n")
    
        conn = connect_db()
        if conn:
            insert_into_db(conn, ip, mac, vendor)
            conn.close()
            
        devices.append((ip, mac, vendor))
            
    return devices

# Funzione per avviare la scansione ARP tramite API Flask
@app.route("/start_scan", methods=["POST"])
def start_scan():
    data = request.json
    target_ip_range = data.get("ip_range")

    if not target_ip_range:
        return jsonify({"error": "Intervallo IP mancante"}), 400
        
    vendor_data = load_vendor_data('mac-vendors-export.json')
    if not vendor_data:
        return jsonify({"error": "Impossibile caricare i dati del vendor"}), 500
                
    conn = connect_db()
    if conn:
        create_table(conn)
        conn.close()
        
    devices = arp_scan(target_ip_range, vendor_data)

    if not devices:
        return jsonify({"message": "Nessun dispositivo trovato"}), 200
    else:
        return jsonify({"devices": devices}), 200

# Funzione principale che esegue la scansione ARP (senza avviare Flask)
def run_scan_directly(target_ip_range):
    vendor_data = load_vendor_data('mac-vendors-export.json')
    if not vendor_data:
        print("Impossibile caricare i dati del vendor")
        return

    conn = connect_db()
    if conn:
        create_table(conn)
        conn.close()

    devices = arp_scan(target_ip_range, vendor_data)

    if not devices:
        print("Nessun dispositivo trovato")
    else:
        print(f"{len(devices)} dispositivi trovati")

if __name__ == "__main__":
    if len(sys.argv) > 1:
        target_ip_range = sys.argv[1]
        run_scan_directly(target_ip_range)  # Esegui la scansione direttamente
    else:
        app.run(host="0.0.0.0", port=5002)  # Avvia il server Flask per l'API

