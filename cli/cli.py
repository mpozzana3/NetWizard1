import socket

# Parametri del server
HOST = '127.0.0.1'  # Indirizzo IP del server (localhost per test)
PORT = 12345         # Porta di connessione

def start_client():
    """Avvia la CLI del client e comunica con il server."""
    # Crea un socket per connettersi al server
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client_socket.connect((HOST, PORT))

    while True:
        # Ricevi il messaggio dal server
        server_message = client_socket.recv(1024).decode()
        print(server_message)

        # Inserisci la scelta dell'utente
        scelta = input("Inserisci la tua scelta (1 o 2): ")

        # Controlla che la scelta sia valida
        while scelta not in {"1", "2"}:
            print("Scelta non valida. Riprova.")
            scelta = input("Scegli il tipo di operazione (1 o 2): ")
        client_socket.send(scelta.encode())

        # Se l'utente ha scelto Scansioni
        if scelta == "1":
            response = client_socket.recv(1024).decode()
            print(response)
            
            # Chiedi al client il nome dell'azienda e la P.IVA
            azienda = input("Inserisci il nome dell'azienda: ")
            p_iva = input("Inserisci la P.IVA dell'azienda: ")

            # Invia i dati al server
            client_socket.send(azienda.encode())
            client_socket.send(p_iva.encode())

            # Ricevi la risposta dal server
            response = client_socket.recv(1024).decode()
            print(response)
            print("Ora digita cli2.py <ip> <porta>")

        # Se l'utente ha scelto Analisi DB
        elif scelta == "2":
            response = client_socket.recv(1024).decode()
            print(response)

        break  # Esci dopo la risposta

    # Chiudi la connessione
    client_socket.close()

if __name__ == "__main__":
    start_client()
