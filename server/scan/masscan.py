import subprocess
import json
import mysql.connector
import sys
import xml.etree.ElementTree as ET
import requests
from datetime import datetime

def get_cidr():
    """Ottiene il CIDR dell'IP pubblico usando ipinfo.io."""
    try:
        response = requests.get("https://ipinfo.io/json", timeout=5)
        data = response.json()
        
        ip = data.get("ip")
        netmask = data.get("netmask", "24") 

        if ip and netmask:
            return f"{ip}/{netmask}"
        else:
            print("Errore: Subnet non disponibile")
            return None
    except requests.RequestException as e:
        print(f"Errore nel recupero del CIDR: {e}")
        return None

def load_config():
    with open("config.json", "r") as f:
        return json.load(f)

def run_masscan(target_ip):
    commands = [
        ["masscan", "-oX", "masscan.xml", "--ports", "0-500", target_ip],
        ["masscan", "-oX", "masscanu.xml", "--ports", "U:0-500", target_ip]
    ]
    
    for cmd in commands:
        try:
            # Esegui il comando e cattura l'output e gli errori
            result = subprocess.run(
                cmd, 
                check=True, 
                stdout=subprocess.PIPE, 
                stderr=subprocess.PIPE, 
                text=True
            )
            
            # Stampa l'output standard
            print(f"Output del comando {cmd}:")
            print(result.stdout)
            
            # Stampa eventuali errori
            if result.stderr:
                print(f"Errori del comando {cmd}:")
                print(result.stderr)
                
        except subprocess.CalledProcessError as e:
            print(f"Errore durante l'esecuzione di Masscan: {e}")
            if e.stderr:
                print(f"Errori: {e.stderr}")

def insert_into_file_scansioni(connection, file_xml,id_scansione):
    try:
        with open(file_xml, "rb") as xml_file:
            xml_content = xml_file.read()

        cursor = connection.cursor()
        insert_query = """
        INSERT INTO file_scansioni (id_scansione, masscanxml)
        VALUES (%s, %s)
        ON DUPLICATE KEY UPDATE 
           masscanxml = VALUES(masscanxml)
        """
        cursor.execute(insert_query, (id_scansione, xml_content))
        connection.commit()
        cursor.close()
        print("File salvati nel database con successo.")
    except FileNotFoundError as e:
        print(f"Errore: {e}")

def connect_db(config):
    db_config = config["db"]
    conn = mysql.connector.connect(
        host=db_config["host"],
        user=db_config["user"],
        password=db_config["password"],
        database=db_config["name"],
        charset="utf8mb4",
        collation="utf8mb4_general_ci"
    )
    return conn

def create_table(conn):
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS masscan (
            id_scansione INT,
            ip VARCHAR(45),
            addrtype VARCHAR(10),
            port_protocol VARCHAR(10),
            portid INT,
            state VARCHAR(10),
            reason VARCHAR(50),
            reason_ttl INT,
            timestamp TEXT,
            PRIMARY KEY (id_scansione, ip, portid)
        )
    """)
    conn.commit()
    cursor.close()

def parse_masscan_xml(file_path, id_scansione):
    tree = ET.parse(file_path)
    root = tree.getroot()
    scan_results = []

    for host in root.findall("host"):
        ip_element = host.find("address")
        ip = ip_element.get("addr")
        addrtype = ip_element.get("addrtype")
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        for port in host.findall("ports/port"):
            port_protocol = port.get("protocol")
            portid = int(port.get("portid"))
            state_element = port.find("state")
            state = state_element.get("state")
            reason = state_element.get("reason")
            reason_ttl = int(state_element.get("reason_ttl"))

            scan_results.append((id_scansione, ip, addrtype, port_protocol, portid, state, reason, reason_ttl, timestamp))
    
    return scan_results

def insert_scan_results(conn, scan_results):
    cursor = conn.cursor()
    cursor.executemany("""
        INSERT INTO masscan (id_scansione, ip, addrtype, port_protocol, portid, state, reason, reason_ttl, timestamp)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
    """, scan_results)
    conn.commit()
    cursor.close()

def main():
    if len(sys.argv) < 2:
        print("Errore: è necessario fornire l'ID della scansione come argomento.")
        return

    print(f"Argomenti ricevuti: {sys.argv}")    
    id_scansione = sys.argv[1]
    config = load_config()
    print(f"configurazione ok")
    print(f"Cerco ip pubblico...")

    target_ip = get_cidr()
    if not target_ip:
        print("Errore: impossibile determinare la subnet pubblica.")
        return

    print(f"Lancio masscan su {target_ip}")    
    run_masscan(target_ip)
    
    conn = connect_db(config)
    create_table(conn)
    
    insert_into_file_scansioni(conn, "masscan.xml", id_scansione)
    scan_results = parse_masscan_xml("masscan.xml", id_scansione)
    insert_scan_results(conn, scan_results)
    
    conn.close()

if __name__ == "__main__":
    main()
