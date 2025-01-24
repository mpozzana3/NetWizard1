import mysql.connector
from mysql.connector import Error
import subprocess
import xml.etree.ElementTree as ET
from datetime import datetime

# Dati per la connessione al database MariaDB
DB_HOST = "localhost"
DB_NAME = "test"
DB_USER = "root"
DB_PASS = "nuova_password"

# Connessione al database MariaDB
def connect_db():
    """Connessione al database MariaDB."""
    try:
        conn = mysql.connector.connect(
            host=DB_HOST,
            database=DB_NAME,
            user=DB_USER,
            password=DB_PASS,
            charset="utf8mb4",
            collation="utf8mb4_general_ci"
        )
        if conn.is_connected():
            print("Connessione al database stabilita.")
        return conn
    except Error as e:
        print(f"Errore nella connessione al database: {e}")
        return None

# Creazione della tabella `nmap`
def create_table(conn):
    """Crea la tabella `nmap` se non esiste già."""
    try:
        cursor = conn.cursor()
        create_table_query = """
        CREATE TABLE IF NOT EXISTS nmap (
            id_scansione INT AUTO_INCREMENT PRIMARY KEY,
            ip VARCHAR(45) DEFAULT NULL,
            timestamp TEXT,
            vendor VARCHAR(255) DEFAULT NULL,
            hostname VARCHAR(255) DEFAULT NULL,
            extraports_count INT DEFAULT NULL,
            extraports_state VARCHAR(255) DEFAULT NULL,
            port_id INT DEFAULT NULL,
            port_script_id VARCHAR(255) DEFAULT NULL,
            port_state VARCHAR(255) DEFAULT NULL,
            port_script_output TEXT DEFAULT NULL,
            port_service_name VARCHAR(255) DEFAULT NULL
        ) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci;
        """
        cursor.execute(create_table_query)
        conn.commit()
        print("Tabella `nmap` creata o già esistente.")
    except Error as e:
        print(f"Errore nella creazione della tabella: {e}")
    finally:
        cursor.close()

# Parsing dei risultati XML di Nmap
from datetime import datetime

# Parsing dei risultati XML di Nmap
def parse_nmap_output(xml_path):
    """Analizza il file XML di output di Nmap e restituisce i dati estratti."""
    try:
        tree = ET.parse(xml_path)
        root = tree.getroot()

        for host in root.findall("host"):
            ip = None
            vendor = None
            hostname = None
            extraports_count = None
            extraports_state = None
            timestamp = None

            # Estrai l'indirizzo IP
            address = host.find("address[@addrtype='ipv4']")
            if address is not None:
                ip = address.get("addr", None)

            # Estrai il vendor dall'indirizzo MAC
            mac_address = host.find("address[@addrtype='mac']")
            if mac_address is not None:
                vendor = mac_address.get("vendor", None)

            # Estrai il primo hostname
            hostnames = host.find("hostnames")
            if hostnames is not None:
                hostname_element = hostnames.find("hostname")
                hostname = hostname_element.get("name", None) if hostname_element is not None else None

            # Estrai il timestamp dal nodo <finished> dentro <runstats>
            runstats = root.find("runstats")
            if runstats is not None:
                finished = runstats.find("finished")
                if finished is not None:
                    timestr = finished.get("timestr", None)  # Estrarre il valore testuale di timestr
                    if timestr:
                        # Convertire il formato `Fri Jan 24 08:52:35 2025` in `YYYY-MM-DD HH:MM:SS`
                        try:
                            timestamp = datetime.strptime(timestr, "%a %b %d %H:%M:%S %Y").strftime("%Y-%m-%d %H:%M:%S")
                        except ValueError:
                            print(f"Formato timestamp non valido: {timestr}")

            # Estrai informazioni sulle porte extra
            extraports = host.find("ports/extraports")
            if extraports is not None:
                extraports_count = extraports.get("count", None)
                extraports_state = extraports.get("state", None)

            # Estrai informazioni sulle porte aperte
            ports = host.find("ports")
            if ports is not None:
                for port in ports.findall("port"):
                    port_id = port.get("portid", None)
                    port_state = port.find("state").get("state") if port.find("state") is not None else None
                    port_service_name = port.find("service").get("name") if port.find("service") is not None else None
                    port_script = port.find("script")
                    port_script_id = port_script.get("id") if port_script is not None else None
                    port_script_output = port_script.get("output") if port_script is not None else None
                    yield (
                        ip,
                        timestamp,
                        vendor,
                        hostname,
                        extraports_count,
                        extraports_state,
                        port_id,
                        port_script_id,
                        port_state,
                        port_script_output,
                        port_service_name,
                    )
    except ET.ParseError as e:
        print(f"Errore nel parsing dell'XML: {e}")
        return []

# Inserimento dei dati nel database
def insert_data(conn, data):
    """Inserisce i dati nella tabella `nmap`."""
    try:
        cursor = conn.cursor()
        insert_query = """
        INSERT INTO nmap (
            ip, timestamp, vendor, hostname, extraports_count, extraports_state,
            port_id, port_script_id, port_state, port_script_output, port_service_name
        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s);
        """
        cursor.execute(insert_query, data)
        conn.commit()
    except Error as e:
        print(f"Errore nell'inserimento dei dati: {e}")
    finally:
        cursor.close()

# Esecuzione di Nmap e parsing dei risultati
def scan_network(target, output_file="scan.xml"):
    """Esegue una scansione di rete con Nmap e salva i risultati in un file XML."""
    try:
        subprocess.run(["nmap", "-oX", output_file, target], check=True)
        print(f"Scansione completata. Risultati salvati in {output_file}")
    except subprocess.CalledProcessError as e:
        print(f"Errore durante l'esecuzione di Nmap: {e}")

# Main
def main():
    conn = connect_db()
    if conn is None:
        return
    create_table(conn)

    # Esegui scansione
    target = "172.16.1.131"  # Modifica con l'intervallo di rete desiderato
    output_file = "scan.xml"
    scan_network(target, output_file)

    # Analizza i risultati e inserisci i dati nel database
    for data in parse_nmap_output(output_file):
        insert_data(conn, data)

    conn.close()

if __name__ == "__main__":
    main()
