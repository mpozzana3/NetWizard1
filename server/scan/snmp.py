import subprocess
import json
import mysql.connector
import re

def load_config():
    with open("config.json", "r") as f:
        return json.load(f)

def parse_nbtscan(file_path):
    """
    Legge il file nbtscan.txt ed estrae gli indirizzi IP dal nuovo formato.
    """
    ip_list = []
    with open(file_path, 'r') as f:
        lines = f.readlines()

    for line in lines:
        if line.strip():
            parts = line.split('§')
            if len(parts) > 0:
                ip = parts[0].strip()
                ip_list.append(ip)

    return ip_list

def run_snmp_check(target_ip, community="public"):
    cmd = ["snmpwalk", "-v", "2c", "-c", community, target_ip]
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        return result.stdout
    except subprocess.CalledProcessError:
        print(f"Errore SNMP su {target_ip}")
        return None

def parse_snmp_output(output):
    parsed_data = {
        "hostname": None,
        "interfaces": [],
        "open_ports": [],
        "processes": []
    }

    if not output:
        return parsed_data

    hostname_match = re.search(r"SNMPv2-MIB::sysName.0 = STRING: (.+)", output)
    if hostname_match:
        parsed_data["hostname"] = hostname_match.group(1)

    interfaces = re.findall(r"IF-MIB::ifDescr\.(\d+) = STRING: (\w+)", output)
    parsed_data["interfaces"] = [{"name": i[1]} for i in interfaces]

    ports = re.findall(r"NET-SNMP-EXTEND-MIB::nsExtendOutLine\.\d+ = STRING: (\d+)", output)
    parsed_data["open_ports"] = [{"port": int(p)} for p in ports]

    processes = re.findall(r"HOST-RESOURCES-MIB::hrSWRunName\.(\d+) = STRING: ([^\n]+)", output)
    parsed_data["processes"] = [{"pid": int(p[0]), "command": p[1]} for p in processes]

    return parsed_data

def connect_db(config):
    db_config = config["db"]
    return mysql.connector.connect(
        host=db_config["host"],
        user=db_config["user"],
        password=db_config["password"],
        database=db_config["name"],
        charset="utf8mb4",
        collation="utf8mb4_general_ci"
    )

def create_table(conn):
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS snmp_scan (
            id INT AUTO_INCREMENT PRIMARY KEY,
            hostname VARCHAR(255),
            interface_name VARCHAR(50),
            port INT,
            pid INT,
            process_cmd TEXT,
            PRIMARY KEY (id, hostname, port)
        )
    """)
    conn.commit()
    cursor.close()

def insert_snmp_results(conn, parsed_data):
    cursor = conn.cursor()

    for interface in parsed_data["interfaces"]:
        cursor.execute("""
            INSERT INTO snmp_scan (hostname, interface_name)
            VALUES (%s, %s)
        """, (parsed_data["hostname"], interface["name"]))

    for port in parsed_data["open_ports"]:
        cursor.execute("""
            INSERT INTO snmp_scan (hostname, port)
            VALUES (%s, %s)
        """, (parsed_data["hostname"], port["port"]))

    for process in parsed_data["processes"]:
        cursor.execute("""
            INSERT INTO snmp_scan (hostname, pid, process_cmd)
            VALUES (%s, %s, %s)
        """, (parsed_data["hostname"], process["pid"], process["command"]))

    conn.commit()
    cursor.close()

def main():
    config = load_config()
    ip_list = parse_nbtscan("nbtscan.txt")
    community = "public"

    conn = connect_db(config)
    create_table(conn)

    for target_ip in ip_list:
        print(f"Eseguo SNMP scan su {target_ip}")
        output = run_snmp_check(target_ip, community)
        parsed_data = parse_snmp_output(output)
        insert_snmp_results(conn, parsed_data)

    conn.close()
    print("Dati SNMP salvati nel database.")

if __name__ == "__main__":
    main()
