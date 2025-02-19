from flask import Flask, render_template, request, jsonify
import json
import socket
import time
import struct

app = Flask(__name__)

SERVER_HOST = "127.0.0.1"
SERVER_PORT = 12346

def load_db_schema():
    with open('db_schema.json') as f:
        return json.load(f)

@app.route('/')
def index():
    schema = load_db_schema()
    tabelle = list(schema['server_centrale'].keys())
    return render_template('index2.html', tabelle=tabelle)

@app.route('/get_columns', methods=['POST'])
def get_columns():
    table_name = request.form.get('table_name')
    schema = load_db_schema()

    if table_name in schema['server_centrale']:
        columns = schema['server_centrale'][table_name]
        column_names = [col['column_name'] for col in columns]
    else:
        column_names = []

    return jsonify(column_names)

@app.route('/submit_query', methods=['POST'])
def submit_query():
    table = request.form.get('table')
    columns = request.form.getlist('column')
    constraint = request.form.get('constraint')

    if not columns:
        columns = ['*']

    query = f"SELECT {', '.join(columns)} FROM {table}"
    if constraint:
        query += f" WHERE {constraint}"

    response = send_query_to_server(query)

    # Processare l'output per eliminare gli "a capo" e troncare il testo se troppo lungo
    max_cell_length = 50  # Imposta una lunghezza massima della cella

    rows = []
    response_lines = response.split('ç')
    
    # Ignorare le prime due righe
    filtered_lines = response_lines[2:]
    
    for row in filtered_lines:
        row = row.strip()  # Rimuoviamo gli spazi extra prima e dopo la riga
        if row:  # Se la riga non è vuota
            print(f"Raw row: {row}")
            
            # Dividere la riga in celle tramite il separatore "§"
            cells = [cell.strip() for cell in row.split('§')]  # Rimuove spazi extra in ogni cella
            print(f"Cells: {cells}")  # Stampa per vedere come vengono suddivise le celle

            # Aggiungi la riga formattata alla lista delle righe
            rows.append(cells)

    return render_template('index2.html', query=query, columns=columns, results=rows)

def send_query_to_server(query):
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.settimeout(10)
            s.connect((SERVER_HOST, SERVER_PORT))
            s.sendall(b"2\n")
            time.sleep(0.1)
            s.sendall(query.encode('utf-8') + b'\n')

            # Prima riceviamo la lunghezza totale del messaggio (4 byte)
            data_length = struct.unpack('!I', s.recv(4))[0]
            print(f"📦 Riceverò {data_length} byte.")

            response = ''
            total_received = 0
            while total_received < data_length:
                chunk = s.recv(min(4096, data_length - total_received)).decode('utf-8', errors='ignore')
                if not chunk:
                    break
                response += chunk
                total_received += len(chunk)
                print(f"Ricevuti {total_received}/{data_length} byte.")

            print("✅ Risposta ricevuta completamente.")
            return response
    except Exception as e:
        return f"Errore nella connessione al server: {e}"


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5006)
