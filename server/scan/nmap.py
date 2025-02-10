import mysql.connector
from mysql.connector import Error
import subprocess
import xml.etree.ElementTree as ET
from datetime import datetime
import sys
import json

# Leggere la configurazione dal file JSON

with open("config.json", "r") as config_file:
    config = json.load(config_file)

# Dati per la connessione al database MariaDB
DB_CONFIG = config["db"]
DB_HOST = DB_CONFIG["host"]
DB_NAME = DB_CONFIG["name"]
DB_USER = DB_CONFIG["user"]
DB_PASS = DB_CONFIG["password"]

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
        if conn.is_connected():
            print("Connessione al database stabilita.")
        return conn
    except Error as e:
        print(f"Errore nella connessione al database: {e}")
        return None

# Creazione della tabella `nmap`      
def create_table(conn):
    try:
        cursor = conn.cursor()
        create_table_query = """
        CREATE TABLE IF NOT EXISTS nmap (
            id_scansione INT,
            ip VARCHAR(45) DEFAULT NULL,
            timestamp TEXT,
            vendor VARCHAR(255) DEFAULT NULL,
            hostname VARCHAR(255) DEFAULT NULL,
            extraports_count INT DEFAULT NULL,
            extraports_state VARCHAR(255) DEFAULT NULL,
            port_id INT DEFAULT NULL,
            port_state VARCHAR(255) DEFAULT NULL,
            port_service_name VARCHAR(255) DEFAULT NULL,
            port_product VARCHAR(255) DEFAULT NULL,
            port_script_id VARCHAR(255) DEFAULT NULL,
            port_script_output TEXT DEFAULT NULL
        ) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci;
        """
        cursor.execute(create_table_query)
        conn.commit()
        print("Tabella `nmap` creata o già esistente.")
    except Error as e:
        print(f"Errore nella creazione della tabella: {e}")
    finally:
        cursor.close()

def parse_nmap_output(xml_path):
    """Analizza il file XML di output di Nmap e restituisce i dati estratti."""
    try:
        tree = ET.parse(xml_path)
        root = tree.getroot()

        for host in root.findall("host"):
            ip, vendor, hostname, timestamp = None, None, None, None
            extraports_count, extraports_state = None, None

            address = host.find("address[@addrtype='ipv4']")
            if address is not None:
                ip = address.get("addr", None)

            mac_address = host.find("address[@addrtype='mac']")
            if mac_address is not None:
                vendor = mac_address.get("vendor", None)

            hostnames = host.find("hostnames")
            if hostnames is not None:
                hostname_element = hostnames.find("hostname")
                hostname = hostname_element.get("name", None) if hostname_element is not None else None

            runstats = root.find("runstats")
            if runstats is not None:
                finished = runstats.find("finished")
                if finished is not None:
                    timestr = finished.get("timestr", None)
                    if timestr:
                        try:
                            timestamp = datetime.strptime(timestr, "%a %b %d %H:%M:%S %Y").strftime("%Y-%m-%d %H:%M:%S")
                        except ValueError:
                            print(f"Formato timestamp non valido: {timestr}")

            extraports = host.find("ports/extraports")
            if extraports is not None:
                extraports_count = extraports.get("count", None)
                extraports_state = extraports.get("state", None)

            ports = host.find("ports")
            if ports is not None:
                for port in ports.findall("port"):
                    port_id = port.get("portid", None)
                    port_state = port.find("state").get("state") if port.find("state") is not None else None
                    service = port.find("service")
                    port_service_name = service.get("name") if service is not None else None
                    port_product = service.get("product") if service is not None else None
                    
                    scripts = port.findall("script")
                    # Ciclo su tutti gli script presenti nella porta
                    if scripts:
                        for script in scripts:
                            port_script_id = script.get("id")
                            port_script_output = script.get("output")
                            yield (
                                ip, timestamp, vendor, hostname, extraports_count, extraports_state,
                                port_id, port_state, port_service_name, port_product, port_script_id, port_script_output
                            )
                    else:
                        # Nessuno script, ma restituire comunque la tupla
                        yield (
                            ip, timestamp, vendor, hostname, extraports_count, extraports_state,
                            port_id, port_state, port_service_name, port_product, None, None
                        )
    except ET.ParseError as e:
        print(f"Errore nel parsing dell'XML: {e}")
        return []

def insert_data(conn, data, id_scansione):
    try:
        print(f"provo a inserire {id_scansione}, {data}")
        cursor = conn.cursor()
        insert_query = """
        INSERT INTO nmap (
            id_scansione, ip, timestamp, vendor, hostname, extraports_count, extraports_state,
            port_id, port_state, port_service_name, port_product, port_script_id, port_script_output
        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s);
        """
        final_data = (id_scansione, *data)
        print(f"Inserting: {final_data}, Length: {len(final_data)}")
        cursor.execute(insert_query, (id_scansione, *data))
        conn.commit()
    except Error as e:
        print(f"Errore nell'inserimento dei dati: {e}")
    finally:
        cursor.close()


def scan_network(target, output_file="scan.xml"):
    try:
        subprocess.run(["nmap","-sC", "-sV", "--stats-every ", "1m", "-oX", output_file, target], check=True)
        print(f"Scansione completata. Risultati salvati in {output_file}")
    except subprocess.CalledProcessError as e:
        print(f"Errore durante l'esecuzione di Nmap: {e}")

def main():
    if len(sys.argv) != 3:
        print("Uso: python nmap.py <id_scansione> <target>")
        sys.exit(1)

    id_scansione = sys.argv[1]
    target = sys.argv[2]

    conn = connect_db()
    if conn is None:
        return
    create_table(conn)

    output_file = "scan.xml"
    scan_network(target, output_file)

    for data in parse_nmap_output(output_file):
        insert_data(conn, data, id_scansione)

    conn.close()

if __name__ == "__main__":
    main()
