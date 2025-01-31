import subprocess
import json
import mysql.connector
import re

def load_config():
    with open("config.json", "r") as f:
        return json.load(f)

def run_snmp_check(target_ip, community="public"):
    cmd = ["snmpwalk", "-v", "2c", "-c", community, target_ip]
    result = subprocess.run(cmd, capture_output=True, text=True, check=True)
    return result.stdout

def parse_snmp_output(output):
    parsed_data = {
        "hostname": None,
        "interfaces": [],
        "open_ports": [],
        "processes": []
    }

    # Estrai il nome host
    hostname_match = re.search(r"SNMPv2-MIB::sysName.0 = STRING: (.+)", output)
    if hostname_match:
        parsed_data["hostname"] = hostname_match.group(1)

    # Estrai le interfacce di rete
    interfaces = re.findall(r"IF-MIB::ifDescr\.(\d+) = STRING: (\w+)", output)
    parsed_data["interfaces"] = [{"name": i[1]} for i in interfaces]

    # Estrai le porte aperte (se sono nel formato snmpwalk per i servizi)
    ports = re.findall(r"NET-SNMP-EXTEND-MIB::nsExtendOutLine\.\d+ = STRING: (\d+)", output)
    parsed_data["open_ports"] = [{"port": int(p)} for p in ports]

    # Estrai i processi (se sono visibili tramite snmpwalk)
    processes = re.findall(r"HOST-RESOURCES-MIB::hrSWRunName\.(\d+) = STRING: ([^\n]+)", output)
    parsed_data["processes"] = [{"pid": int(p[0]), "command": p[1]} for p in processes]

    return parsed_data

def connect_db(config):
    db_config = config["db"]
    conn = mysql.connector.connect(
        host=db_config["host"],
        user=db_config["user"],
        password=db_config["password"],
        database=db_config["name"]
    )
    return conn

def create_table(conn):
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS snmp_scan (
            id INT AUTO_INCREMENT PRIMARY KEY,
            hostname VARCHAR(255),
            interface_name VARCHAR(50),
            port INT,
            pid INT,
            process_cmd TEXT
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
    target_ip = "172.16.1.131"  # Modifica con l'IP target
    community = "public"  # Modifica se necessario

    output = run_snmp_check(target_ip, community)
    parsed_data = parse_snmp_output(output)

    conn = connect_db(config)
    create_table(conn)
    insert_snmp_results(conn, parsed_data)

    conn.close()
    print("Dati SNMP salvati nel database.")

if __name__ == "__main__":
    main()
