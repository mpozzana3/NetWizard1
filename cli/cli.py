import sys
import socket

HOST = 'localhost'  # Indirizzo del server
PORT = 12345         # Porta del server

def recv_message(sock):
    """Riceve un messaggio dal server gestendo errori di connessione."""
    try:
        return sock.recv(1024).decode().strip()
    except (socket.error, ConnectionResetError):
        print("Errore di connessione. Chiudo il client.")
        sock.close()
        exit(1)

def start_client():
    """Avvia la CLI del client e comunica con il server."""
    # Crea un socket per connettersi al server
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client_socket.connect((HOST, PORT))

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
            response = recv_message(client_socket)
            print(response)

            # Chiedi al client il nome dell'azienda e la P.IVA
            azienda = input("Inserisci il nome dell'azienda: ").strip()
            p_iva = input("Inserisci la P.IVA dell'azienda: ").strip()

            # Invia i dati al server
            client_socket.sendall(azienda.encode())
            client_socket.sendall(p_iva.encode())

            # Ricevi il messaggio con le opzioni di scansione
            print("Inizio a ricevere il messaggio con le opzioni di scansione...")
            server_message = recv_message(client_socket)
            print("Messaggio ricevuto dal server:", server_message)

            if server_message == "Azienda non trovata o non valida.":
             print("Chiusura connessione...")
             client_socket.close()
             return

            # Inserisci la scelta della scansione
            print("A questo punto dovrebbe arrivare la richiesta per inserire la scelta.")
            sys.stdout.flush()  # Forza il flush dell'output
            scelta_scansione = input("Inserisci la tua scelta: ").strip()

            print(f"Scelta inserita: {scelta_scansione}")
            client_socket.sendall(scelta_scansione.encode())
            print(f"Scelta della scansione inviata: {scelta_scansione}")
            sys.stdout.flush()

            # Ricevi conferma della scelta dal server
            validita = recv_message(client_socket)
            print(validita)

            # Ricevi stato della scansione
            response = recv_message(client_socket)
            print(response)

            response = recv_message(client_socket)
            print(response)

    # Se l'utente ha scelto Analisi DB
    elif scelta == "2":
        tables_message = client_socket.recv(1024).decode()
        print(tables_message)

        # Chiedi all'utente di scegliere una tabella
        tab = input("Seleziona una tabella: ").strip()
        client_socket.send(tab.encode())

        # Ricevi l'elenco delle colonne per la tabella scelta
        columns_message = client_socket.recv(1024).decode()
        print(columns_message)

        # Chiedi all'utente di selezionare le colonne
        col = input("Seleziona le colonne da includere (o '*' per tutte): ").strip()
        client_socket.send(col.encode())

        # Ricevi il messaggio riguardante il vincolo opzionale
        constraint_message = client_socket.recv(1024).decode()
        print(constraint_message)

        # Chiedi se l'utente vuole applicare un vincolo opzionale
        vincolo = input("Indica un vincolo opzionale: ").strip()
        client_socket.send(vincolo.encode())

        # Ricevi il risultato della query dal server
        data = []
        while True:
            chunk = client_socket.recv(8192).decode()  # Buffer più grande
            if not chunk:  # Se non riceve più dati, esce
                break
            data.append(chunk)

        server_response = "".join(data)
        print(f"Risultato della query: {server_response}")

    # Chiudi la connessione
    client_socket.close()

if __name__ == "__main__":
    start_client()
