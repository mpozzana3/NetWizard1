import sys
import os
import subprocess
from flask import Flask, request, jsonify

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../server')))

app = Flask(__name__)

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

    else:
        return jsonify({"error": f"Comando '{command}' non supportato"}), 400

    return jsonify({"result": result})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5001)
