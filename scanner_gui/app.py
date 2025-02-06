from flask import Flask, render_template, request, redirect, url_for, session, jsonify
import socket

app = Flask(__name__)
app.secret_key = 'your_secret_key'

SERVER_HOST = '127.0.0.1'
SERVER_PORT = 12346  

def send_to_server(choice, azienda=None, p_iva=None, scan_type=None):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.connect((SERVER_HOST, SERVER_PORT))
        response1 = s.recv(1024).decode()
        s.sendall(choice.encode())
        response2 = s.recv(1024).decode()
        response3, extra_message = "", ""

        if choice == '1' and azienda and p_iva:
            s.sendall(f"{azienda}|{p_iva}".encode())
            response3 = s.recv(1024).decode()  # Riceve la conferma dell'azienda scelta
            extra_message = s.recv(1024).decode()  # Riceve la richiesta di scelta della scansione
            
            # In questa parte, non inviamo scan_type se è None
            if scan_type:
                s.sendall(scan_type.encode())  # Questo accade solo nella seconda chiamata

        return response1, response2, response3, extra_message

@app.route('/')
def index():
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.connect((SERVER_HOST, SERVER_PORT))
        response = s.recv(1024).decode()
    return render_template('index.html', response=response)

@app.route('/send_scan', methods=['POST'])
def send_scan():
    azienda, p_iva = request.form.get('azienda'), request.form.get('p_iva')
    # Chiamata al server senza inviare scan_type
    _, _, response3, extra_message = send_to_server('1', azienda, p_iva)  # scan_type non viene passato
    session['response3'], session['extra_message'] = response3, extra_message
    return redirect(url_for('select_scan_type'))  # Redirigi alla pagina di selezione del tipo di scansione

@app.route('/select_scan_type')
def select_scan_type():
    return render_template('scan_result.html', response3=session.get('response3', 'No data received'), extra_message=session.get('extra_message', 'No extra message'))

@app.route('/analisi_db')
def analisi_db():
    # Invia la scelta '2' al server per analisi DB
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.connect((SERVER_HOST, SERVER_PORT))
        s.sendall('2'.encode())  # Scelta 2 per Analisi DB
        response1 = s.recv(1024).decode()  # Riceve la risposta dal server

    # Salva la risposta del server nella sessione
    session['server_message'] = response1
    
    # Redirigi alla pagina di input per la risposta
    return redirect(url_for('input_response'))

@app.route('/input_response', methods=['GET', 'POST'])
def input_response():
    if request.method == 'POST':
        # Ottieni la risposta dell'utente dal form
        user_response = request.form.get('user_response')
        print(f"Risposta dell'utente: {user_response}")
        
        # Invia la risposta al server per elaborarla
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.connect((SERVER_HOST, SERVER_PORT))
            s.sendall(user_response.encode())  # Invia la risposta al server
            server_acknowledgment = s.recv(1024).decode()  # Riceve una conferma dal server
            print(f"Conferma dal server: {server_acknowledgment}")
        
        # Dopo aver inviato la risposta, puoi reindirizzare a una pagina finale
        return redirect(url_for('select_scan_type'))  # O qualsiasi altra pagina finale

    # In GET, mostra il messaggio ricevuto dal server
    message = session.get('server_message', 'Nessun messaggio ricevuto')
    return render_template('input_response.html', message=message)

@app.route('/send_scan_type', methods=['POST'])
def send_scan_type():
    scan_type = request.form.get('scan_type')
    # Ora invii anche scan_type
    _, _, response3, extra_message = send_to_server('1', azienda=session.get('azienda'), p_iva=session.get('p_iva'), scan_type=scan_type)
    return redirect(url_for('scan_result'))  # Redirigi alla pagina di risultato della scansione

if __name__ == "__main__":
    app.run(debug=True, host='0.0.0.0', port=5005)
