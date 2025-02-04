from flask import Flask, render_template, request, jsonify
import socket

app = Flask(__name__)

SERVER_HOST = '127.0.0.1'
SERVER_PORT = 12346  

def send_to_server(choice, azienda=None, p_iva=None):
    """Invia la scelta o i dati al server e riceve la risposta."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.connect((SERVER_HOST, SERVER_PORT))
        response1 = s.recv(1024).decode()  # Messaggio iniziale
        s.sendall(choice.encode())  # Invia scelta
        response2 = s.recv(1024).decode()  # Risposta alla scelta

        response3 = ""
        if choice == '1' and azienda and p_iva:
            dati = f"{azienda}|{p_iva}"
            s.sendall(dati.encode())  
            response3 = s.recv(1024).decode()  

        return response1, response2, response3

@app.route('/')
def index():
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.connect((SERVER_HOST, SERVER_PORT))
        response = s.recv(1024).decode()  
        return render_template('index.html', response=response)

@app.route('/send_choice', methods=['POST'])
def send_choice():
    choice = request.form.get('choice')
    response1, response2, _ = send_to_server(choice)
    return jsonify({"response1": response1, "response2": response2, "choice": choice})

@app.route('/send_scan', methods=['POST'])
def send_scan():
    azienda = request.form.get('azienda')
    p_iva = request.form.get('p_iva')
    _, _, response3 = send_to_server('1', azienda, p_iva)
    return jsonify({"response3": response3})

if __name__ == "__main__":
    app.run(debug=True, host='0.0.0.0', port=5005)
