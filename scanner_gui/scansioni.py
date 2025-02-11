from flask import Flask, render_template, request, jsonify
import socket

app = Flask(__name__)

SERVER_HOST = "127.0.0.1"
SERVER_PORT = 12346

# Invia un messaggio iniziale al server
def send_initial_message():
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        try:
            s.connect((SERVER_HOST, SERVER_PORT))
            print("📡 Connessione al server stabilita, invio segnale iniziale...")
            s.sendall(b"1")
        except Exception as e:
            print(f"❌ Errore di connessione: {e}")

send_initial_message()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/send_data', methods=['POST'])
def send_data():
    data = request.json
    azienda = data.get("azienda", "")
    p_iva = data.get("p_iva", "")
    scan_type = data.get("scan_type", "")

    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            print(f"📡 Connessione al server {SERVER_HOST}:{SERVER_PORT}...")
            s.connect((SERVER_HOST, SERVER_PORT))
            
            # Formatta correttamente i dati
            dati_da_inviare = f"{azienda}|{p_iva}|{scan_type}"
            print(f"📤 Invio dati: {dati_da_inviare}")
            s.sendall(dati_da_inviare.encode())

            responses = []
            for i in range(3):
                response = s.recv(1024).decode().strip()
                if response:
                    print(f"📩 Ricevuto dal server [{i+1}]: {response}")
                    responses.append(response)
                else:
                    print(f"⚠️ Nessuna risposta ricevuta alla {i+1}ª richiesta.")

            return jsonify({"responses": responses})
    except Exception as e:
        print(f"❌ Errore durante la comunicazione: {e}")
        return jsonify({"error": str(e)})

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5005)
