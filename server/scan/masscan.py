import subprocess
import json
import mysql.connector
import sys
import xml.etree.ElementTree as ET

def load_config():
    with open("config.json", "r") as f:
        return json.load(f)

def run_masscan(target_ip):
    commands = [
        ["masscan", "-oX", "masscan.xml", "--ports", "0-500", target_ip],
        ["masscan", "-oX", "masscanu.xml", "--ports", "U:0-500", target_ip]
    ]
    
    for cmd in commands:
        subprocess.run(cmd, check=True)

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
            timestamp INT
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
        timestamp = int(host.get("endtime"))

        for port in host.findall("ports/port"):
            port_protocol = port.get("protocol")
            portid = int(port.get("portid"))
            state_element = port.find("state")
            state = state_element.get("state")
            reason = state_element.get("reason")
            reason_ttl = int(state_element.get("reason_ttl"))

            # Aggiungi l'ID della scansione ai risultati
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
    # Verifica che l'ID della scansione sia stato passato come argomento
    if len(sys.argv) < 2:
        print("Errore: è necessario fornire l'ID della scansione come argomento.")
        return
    
    # Prendi l'ID della scansione dalla riga di comando
    id_scansione = sys.argv[1]

    config = load_config()
    target_ip = "31.156.174.90/30"
    
    run_masscan(target_ip)
    
    conn = connect_db(config)
    create_table(conn)
    
    scan_results = parse_masscan_xml("masscan.xml", id_scansione)
    insert_scan_results(conn, scan_results)
    
    conn.close()

if __name__ == "__main__":
    main()
