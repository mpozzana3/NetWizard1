from flask import Flask, render_template, request, jsonify
import json
import socket
import time

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

    # Convertire la risposta in una lista di liste per DataTables
    rows = [row.split(',') for row in response.split('\n') if row]

    return render_template('index2.html', query=query, columns=columns, results=rows)

def send_query_to_server(query):
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.settimeout(5)
            s.connect((SERVER_HOST, SERVER_PORT))
            s.sendall(b"2\n")
            time.sleep(0.1)
            s.sendall(query.encode('utf-8') + b'\n')

            response = ''
            while True:
                chunk = s.recv(4096).decode('utf-8')
                response += chunk
                if len(chunk) < 4096:
                    break

            return response
    except Exception as e:
        return f"Errore nella connessione al server: {e}"

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5006)
