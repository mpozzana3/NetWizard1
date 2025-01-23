import socket

# Configurazione del client socket
HOST = "localhost"  # Indirizzo del server
PORT = 5003  # Porta del server

def start_cli():
    """Avvia la CLI e comunica con il server."""
    # Crea un socket per connettersi al server
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client_socket.connect((HOST, PORT))

    while True:
        # Ricevi il messaggio di benvenuto
        response = client_socket.recv(1024).decode()
        print(response)

        # Inserisci il nome dell'azienda
        azienda = input("Inserisci il nome dell'azienda: ")
        client_socket.send(azienda.encode())

        # Inserisci la P.IVA
        p_iva = input("Inserisci la P.IVA: ")
        client_socket.send(p_iva.encode())

        # Ricevi la risposta dal server
        response = client_socket.recv(1024).decode()
        print(response)

        # Se i dati sono corretti, esci dal ciclo
        if "Dati ricevuti e inseriti correttamente. Procedo con la scansione." in response or "La P.IVA è già associata. Procedo con la scansione." in response:
            break

    while True:
        # Ricevi il messaggio di scansione
        response = client_socket.recv(1024).decode()
        print(f"Messaggio ricevuto dal server: {response}")

        # Scegli il tipo di scansione
        scelta_scansione = input("Scegli il tipo di scansione (1-4): ")

        # Controlla che la scelta sia valida
        while scelta_scansione not in {"1", "2", "3", "4"}:
            print("Scelta non valida. Riprova.")
            scelta_scansione = input("Scegli il tipo di scansione (1-4): ")  # Chiedi di nuovo se la scelta è invalida

        # Se la scelta è valida, invia la risposta al server
        client_socket.send(scelta_scansione.encode())
        print(f"Scansione scelta: {scelta_scansione}")

        # Ricevi la risposta dal server
        response = client_socket.recv(1024).decode()
        print(f"Risposta ricevuta: {response}")

        break  # Esci dal ciclo dopo aver scelto la scansione

    # Chiudi la connessione
    client_socket.close()


if __name__ == "__main__":
    start_cli()
