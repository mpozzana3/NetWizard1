import json
import mysql.connector

def load_config():
    """Carica la configurazione dal file JSON."""
    with open('config.json', 'r') as f:
        return json.load(f)

def create_db_connection(config):
    """Crea una connessione al database MariaDB."""
    try:
        connection = mysql.connector.connect(
            host=config['db']['host'],
            user=config['db']['user'],
            password=config['db']['password'],
            database=config['db']['name'],
            charset="utf8mb4",
            collation="utf8mb4_general_ci"
        )
        return connection
    except mysql.connector.Error as e:
        print(f"Errore nella connessione al database: {e}")
        return None

def create_tables(connection):
    """Crea le tabelle nel database."""
    queries = [
        """
        CREATE TABLE IF NOT EXISTS nbtscan (
            id_scansione VARCHAR(255),
            ip VARCHAR(15) NOT NULL,
            netbios_name VARCHAR(255),
            server VARCHAR(255),
            user VARCHAR(255),
            mac_address VARCHAR(17),
            timestamp TEXT,
            PRIMARY KEY (id_scansione, ip)
        )
        """,
        """
        CREATE TABLE IF NOT EXISTS scansioni (
            id_scansione INT AUTO_INCREMENT,
            p_iva VARCHAR(255) NOT NULL,
            timestamp TEXT NOT NULL,
            tipo_scansione VARCHAR(255) NOT NULL,
            stato INT NOT NULL,
            PRIMARY KEY (id_scansione)
        )
        """,
        """
        CREATE TABLE IF NOT EXISTS enum4linux (
            id_scansione VARCHAR(255) NOT NULL,
            ip VARCHAR(15),
            credentials TEXT,
            listeners TEXT,
            domain TEXT,
            nmblookup TEXT,
            errors TEXT,
            timestamp TEXT,
            PRIMARY KEY (id_scansione, ip)
        )
        """,
        """
        CREATE TABLE IF NOT EXISTS extended_enum (
            id_scansione VARCHAR(255) NOT NULL,
            ip VARCHAR(15) NOT NULL,
            json_data TEXT,
            timestamp TEXT,
            PRIMARY KEY (id_scansione, ip)
        )
        """,
        """
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
        """,
        """
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
        )
        """,
        """
        CREATE TABLE IF NOT EXISTS tabella_host (
            id_scansione VARCHAR(255),
            ip VARCHAR(15),
            mac_address VARCHAR(17),
            timestamp TEXT,
            vendor VARCHAR(255),
            tipo_scansione VARCHAR(255) DEFAULT NULL,
            PRIMARY KEY (id_scansione, mac_address)
        )
        """,
        """
        CREATE TABLE IF NOT EXISTS smbclient (
            id_scansione VARCHAR(255) NOT NULL,
            ip VARCHAR(15) NOT NULL,
            login_anonimo VARCHAR(20) NOT NULL,
            timestamp TEXT,
            PRIMARY KEY (id_scansione, ip)            
        )
        """,
        """
        CREATE TABLE IF NOT EXISTS file_scansioni (
            id_scansione INT,
            nmapxml LONGTEXT,
            enum4json LONGTEXT,
            masscanxml LONGTEXT,
            nmaphtml LONGTEXT,
            PRIMARY KEY (id_scansione)
        )
        """,
        """
        CREATE TABLE IF NOT EXISTS stdout (
            id_scansione INT NOT NULL,
            stdout LONGTEXT,
            PRIMARY KEY (id_scansione)
        )
        """,
        """
        CREATE TABLE IF NOT EXISTS smbmap (
            id_scansione INT NOT NULL,
            ip VARCHAR(255) NOT NULL,
            Share VARCHAR(255),
            Privs VARCHAR(255),
            Comment TEXT,
            timestamp TEXT,
            PRIMARY KEY (id_scansione, ip, Share)
        )
        """,
        """
        CREATE TABLE IF NOT EXISTS snmp_scan (
            id INT AUTO_INCREMENT,
            hostname VARCHAR(255),
            interface_name VARCHAR(50),
            port INT,
            pid INT,
            process_cmd TEXT,
            PRIMARY KEY (id, hostname, port)
        )
        """
    ]
    try:
        cursor = connection.cursor()
        for query in queries:
            cursor.execute(query)
        connection.commit()
        cursor.close()
        print("Tabelle create con successo.")
    except mysql.connector.Error as e:
        print(f"Errore nella creazione delle tabelle: {e}")

def main():
    config = load_config()
    connection = create_db_connection(config)
    if connection:
        create_tables(connection)
        connection.close()

if __name__ == "__main__":
    main()
