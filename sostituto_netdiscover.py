import psycopg2
from scapy.all import ARP, sniff
from macaddress import get_mac_vendor  # Importa il modulo

# Dati per la connessione al database PostgreSQL 
DB_HOST = "localhost"  # Host del database
DB_NAME = "tirocinio"  # Nome del database
DB_USER = "postgres"  # Nome utente per il database
DB_PASS = "20134"  # Password per l'utente del database
              
# File per salvare i risultati
output_file = "test.txt"

# Connessione al database PostgreSQL
def connect_db():
    """Connessione al database PostgreSQL."""
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
        
# Funzione per creare la tabella se non esiste
def create_table(conn): 
    """Crea la tabella per memorizzare i dati ARP se non esiste."""
    with conn.cursor() as cursor:
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS arp_data (
                id SERIAL PRIMARY KEY,
                ip VARCHAR(15),
                mac VARCHAR(17),
                vendor VARCHAR(255),
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """)
        conn.commit()

# Funzione per inserire i dati nella tabella
def insert_into_db(conn, ip, mac, vendor):
    """Inserisce i dati ARP nella tabella del database."""
    with conn.cursor() as cursor:
        cursor.execute("""
            INSERT INTO arp_data (ip, mac, vendor) VALUES (%s, %s, %s);
        """, (ip, mac, vendor))
        conn.commit()
            
def process_packet(packet):
    """Elabora i pacchetti ARP per individuare dispositivi attivi e salvarli nel file e nel database."""
    if ARP in packet and packet[ARP].op in (1, 2):  # ARP request (1) o reply (2)
        mac = packet[ARP].hwsrc
        ip = packet[ARP].psrc
        print(f"IP: {ip} - MAC: {mac}")

        # Recupera il vendor del MAC usando la funzione dal modulo macaddress.py
        vendor = get_mac_vendor(mac)
        
        # Salva nel file
        with open(output_file, "a") as f:
            f.write(f"IP: {ip} - MAC: {mac} - Vendor: {vendor}\n")
        
        # Inserisci nel database
        conn = connect_db()
        if conn:
            insert_into_db(conn, ip, mac, vendor)
            conn.close()
              
def main(): 
    # Connessione al database
    conn = connect_db()
    if conn:
        create_table(conn)
        conn.close()
    
    print("Sniffing ARP packets. Premere Ctrl+C per interrompere.")
    try:
        # Avvia lo sniffing sulla rete per pacchetti ARP
        sniff(filter="arp", prn=process_packet, store=False)
    except KeyboardInterrupt:
        print("\nInterrotto dallo user.")
    
if __name__ == "__main__":
    main()
