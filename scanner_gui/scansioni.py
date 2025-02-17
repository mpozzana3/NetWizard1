from flask import Flask, render_template, request, Response, jsonify
import socket
import time

app = Flask(__name__)

SERVER_HOST = "127.0.0.1"
SERVER_PORT = 12346

client_data = {}

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/send_data', methods=['POST'])
def send_data():
    global client_data
    data = request.json
    client_data = {
        "azienda": data.get("azienda", ""),
        "p_iva": data.get("p_iva", ""),
        "scan_type": data.get("scan_type", "")
    }
    print(f"📤 Ricevuti dati: {client_data}")
    return jsonify({"message": "Dati ricevuti, inizio scansione..."})

@app.route('/stream')
def stream():
    def event_stream():
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                print(f"📡 Connessione al server {SERVER_HOST}:{SERVER_PORT}...")
                s.connect((SERVER_HOST, SERVER_PORT))

                s.sendall(b"1\n")  # Invia il primo messaggio
                print("Initial message sent")

                time.sleep(0.1)

                dati_da_inviare = f"{client_data['azienda']}|{client_data['p_iva']}|{client_data['scan_type']}"
                print(f"📤 Invio dati: {dati_da_inviare}")
                s.sendall(dati_da_inviare.encode())

                for i in range(4):
                    response = s.recv(1024).decode().strip()
                    if response:
                        print(f"📩 Ricevuto dal server [{i+1}]: {response}")
                        yield f"data: {response}\n\n"
                        time.sleep(0.1)  # Simula un'attesa tra i messaggi
                    else:
                        print(f"⚠️ Nessuna risposta ricevuta alla {i+1}ª richiesta.")

        except Exception as e:
            print(f"❌ Errore durante la comunicazione: {e}")
            yield f"data: Errore: {e}\n\n"

    return Response(event_stream(), mimetype='text/event-stream')

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5005)
