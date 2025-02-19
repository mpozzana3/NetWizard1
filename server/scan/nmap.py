import mysql.connector
from mysql.connector import Error
import subprocess
import xml.etree.ElementTree as ET
from datetime import datetime
import sys
import json
import os

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

# Funzione per inserire il file di output nella tabella file scansioni
def insert_into_file_scansioni(connection, id_scansione, xml_path, html_path):
    try:
        with open(xml_path, "rb") as xml_file:
            xml_content = xml_file.read()
        with open(html_path, "rb") as html_file:
            html_content = html_file.read()

        cursor = connection.cursor()
        insert_query = """
        INSERT INTO file_scansioni (id_scansione, nmapxml, nmaphtml)
        VALUES (%s, %s, %s)
        ON DUPLICATE KEY UPDATE 
           nmapxml = VALUES(nmapxml), 
           nmaphtml = VALUES(nmaphtml);
        """
        cursor.execute(insert_query, (id_scansione, xml_content, html_content))
        connection.commit()
        cursor.close()
        print("File salvati nel database con successo.")
    except FileNotFoundError as e:
        print(f"Errore: {e}")

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
        cursor = conn.cursor()
        insert_query = """
        INSERT INTO nmap (
            id_scansione, ip, timestamp, vendor, hostname, extraports_count, extraports_state,
            port_id, port_state, port_service_name, port_product, port_script_id, port_script_output
        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s);
        """
        final_data = (id_scansione, *data)
        cursor.execute(insert_query, (id_scansione, *data))
        conn.commit()
    except Error as e:
        print(f"Errore nell'inserimento dei dati: {e}")
    finally:
        cursor.close()

def scan_network(target, output_file="scan.xml"):
    try:
        # Esegui il comando Nmap e cattura l'output e gli errori
        result = subprocess.run(
            ["nmap", "-sC", "-sV", "--stats-every", "1m", "--stylesheet", "https://raw.githubusercontent.com/Haxxnet/nmap-bootstrap-xsl/main/nmap-bootstrap.xsl", "-oX", output_file, target],
            check=True, 
            stdout=subprocess.PIPE, 
            stderr=subprocess.PIPE, 
            text=True
        )
        
        # Stampa l'output standard
        print(f"Scansione completata. Risultati salvati in {output_file}")
        print("Output della scansione Nmap:")
        print(result.stdout)
        
        # Stampa eventuali errori
        if result.stderr:
            print("Errori durante la scansione Nmap:")
            print(result.stderr)
            
    except subprocess.CalledProcessError as e:
        print(f"Errore durante l'esecuzione di Nmap: {e}")
        if e.stderr:
            print(f"Errori: {e.stderr}")

def generate_html_report(output_file="scan.xml"):
    try:
        # Scarica il foglio di stile XSLT localmente
        xslt_file = "nmap-bootstrap.xsl"
        if not os.path.exists(xslt_file):
            subprocess.run(["wget", "https://raw.githubusercontent.com/Haxxnet/nmap-bootstrap-xsl/main/nmap-bootstrap.xsl", "-O", xslt_file], check=True)
        
        # Genera il file HTML usando xsltproc
        html_file = "report.html"
        subprocess.run(["xsltproc", "-o", html_file, xslt_file, output_file], check=True)
        print(f"File HTML generato con successo: {html_file}")
        return html_file
    except subprocess.CalledProcessError as e:
        print(f"Errore durante la generazione del report HTML: {e}")

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

    # Genera il report HTML dopo la scansione
    nmap_html = generate_html_report(output_file)

    insert_into_file_scansioni(conn, id_scansione, output_file, nmap_html)

    for data in parse_nmap_output(output_file):
        insert_data(conn, data, id_scansione)

    conn.close()

if __name__ == "__main__":
    main()

