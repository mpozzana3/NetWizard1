import socket
from flask import Flask, render_template, request, jsonify

app = Flask(__name__)

SERVER_HOST = "127.0.0.1"
SERVER_PORT = 12346

def send_message(msg):
    """Invia un messaggio al server e riceve la risposta."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        try:
            s.connect((SERVER_HOST, SERVER_PORT))
            s.sendall(msg.encode())
            response = s.recv(4096).decode()
            return response
        except Exception as e:
            return f"Errore: {e}"

@app.route('/', methods=['GET', 'POST'])
def index():
    """Pagina principale che invia '2' al server e mostra la GUI."""
    response = send_message("2|")
    tabelle = response.split("\n")[1:]  # Estraggo solo i nomi delle tabelle
    return render_template('index2.html', tabelle=tabelle)

@app.route('/get_columns', methods=['POST'])
def scegli_tabella():
    """Invia la tabella scelta e riceve le colonne disponibili."""
    data = request.json
    tabella = data.get("tabella")
    response = send_message(f"2|{tabella}||")  # Invia tabella scelta
    colonne = response.split("\n")[1:]  # Estraggo i nomi delle colonne
    print(f"colonne ricevute:{colonne}")
    return render_template('index2.html', tabelle=[], colonne=colonne, tabella=tabella)

@app.route('/scegli_colonne', methods=['POST'])
def scegli_colonne():
    """Invia la scelta delle colonne e il vincolo al server."""
    tabella = request.form['tabella']
    colonne = request.form.getlist('colonne')  # Lista colonne selezionate
    vincolo = request.form['vincolo']

    colonne_str = ",".join(colonne) if colonne else "*"
    messaggio = f"2|{tabella}|{colonne_str}|{vincolo}"
    risultato = send_message(messaggio)

    return render_template('index2.html', tabelle=[], colonne=[], tabella=tabella, risultato=risultato)

if __name__ == "__main__":
    app.run(debug=True, host='0.0.0.0', port=5006)
