import sys
import os
import subprocess
import mysql.connector
from flask import Flask, request, jsonify

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../server')))

# Dati per la connessione al database MariaDB
DB_HOST = "localhost"
DB_NAME = "test"
DB_USER = "root"
DB_PASS = "nuova_password"

app = Flask(__name__)

def connect_db():
    """Crea una connessione al database MariaDB."""
    try:
        conn = mysql.connector.connect(
            host=DB_HOST,
            database=DB_NAME,
            user=DB_USER,
            password=DB_PASS,
            charset="utf8mb4",
            collation="utf8mb4_general_ci"
        )
        return conn
    except mysql.connector.Error as e:
        print(f"Errore nella connessione al database: {e}")
        return None

def create_table_if_not_exists():
    """Crea la tabella se non esiste già."""
    conn = connect_db()
    if conn:
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS aziende (
                id INT AUTO_INCREMENT PRIMARY KEY,
                azienda VARCHAR(255) NOT NULL,
                p_iva VARCHAR(255) NOT NULL UNIQUE
            );
        """)
        conn.commit()
        cursor.close()
        conn.close()

def insert_company_data(azienda, p_iva):
    """Inserisce i dati azienda e P.IVA nel database se non esistono già."""
    conn = connect_db()
    if conn:
        cursor = conn.cursor()
        try:
            cursor.execute("INSERT IGNORE INTO aziende (azienda, p_iva) VALUES (%s, %s)", (azienda, p_iva))
            conn.commit()
            cursor.close()
            conn.close()
            return True
        except mysql.connector.Error as e:
            print(f"Errore nell'inserimento dei dati: {e}")
            cursor.close()
            conn.close()
            return False
    return False

@app.route("/execute", methods=["POST"])
def execute():
    data = request.json
    command = data.get("command")
    args = data.get("args", [])

    if not command:
        return jsonify({"error": "Comando mancante"}), 400

    # Logica dei comandi
    if command == "echo":
        result = " ".join(args)
    elif command == "add":
        try:
            numbers = list(map(int, args))
            result = sum(numbers)
        except ValueError:
            return jsonify({"error": "Argomenti non validi per add"}), 400
    elif command == "start":
        result = "Collegamento riuscito.\nAzienda e P.IVA richiesti."
        return jsonify({"result": result})
    elif command == "start-scan":
        try:
            # Esegui lo script di scansione ARP
            subprocess.run(['python3', 'scan/scan-1.py'], check=True)
            result = "Scansione ARP avviata correttamente."
        except subprocess.CalledProcessError:
            return jsonify({"error": "Errore nell'avvio della scansione ARP"}), 500
    elif command == "start-scan2":
        try:
            # Prendi l'intervallo IP dagli argomenti
            ip_range = args[0] if args else None
            if not ip_range:
                return jsonify({"error": "Intervallo IP mancante"}), 400

            # Passa l'intervallo IP a scan-2.py
            subprocess.run(['python3', 'scan/scan-2.py', ip_range], check=True)
            result = f"Scansione ARP con scan-2.py avviata per {ip_range}."
        except subprocess.CalledProcessError:
            return jsonify({"error": "Errore nell'avvio della scansione ARP con scan-2.py"}), 500
    elif command == "start-nmap-scan":
        try:
            # Prendi l'intervallo IP dagli argomenti
            ip_range = args[0] if args else None
            if not ip_range:
                return jsonify({"error": "Intervallo IP mancante"}), 400
            # Esegui la scansione NMAP
            result = subprocess.run(
                ['sudo', 'nmap', '-sV', '-sC', '-v', '-d', '--script-timeout', '30s', '--script=vuln', '-oA', 'nmap-vuln', ip_range],
                capture_output=True, text=True
            )

            if result.returncode != 0:
                # Se nmap fallisce, restituisci l'errore
                return jsonify({"error": f"Errore nell'esecuzione di NMAP: {result.stderr}"}), 500

            result = f"Scansione NMAP completata per {ip_range}. Risultati: {result.stdout}"
        except Exception as e:
            return jsonify({"error": f"Errore nell'esecuzione di NMAP: {str(e)}"}), 500
    elif command == "start-scan-completa":
        try:
            # Prendi l'intervallo IP dagli argomenti
            ip_range = args[0] if args else None
            if not ip_range:
                return jsonify({"error": "Intervallo IP mancante"}), 400

            # Esegui le tre scansioni in sequenza
            subprocess.run(['python3', 'scan/scan-1.py'], check=True)
            subprocess.run(['python3', 'scan/scan-2.py', ip_range], check=True)
            subprocess.run(['sudo', 'nmap', '-sV', '-sC', '-v', '-d', '--script-timeout', '30s', '--script=vuln', '-oA', 'nmap-vuln', ip_range], check=True)

            result = "Scansioni complete avviate e completate con successo."
        except subprocess.CalledProcessError as e:
            return jsonify({"error": f"Errore durante l'esecuzione delle scansioni: {str(e)}"}), 500

    else:
        return jsonify({"error": f"Comando '{command}' non supportato"}), 400

    return jsonify({"result": result})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5001)
