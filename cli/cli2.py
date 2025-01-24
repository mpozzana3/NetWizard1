import socket
import sys

def start_client(server_ip, server_port):
    """Avvia la CLI del client e comunica con il server."""
    try:
        # Crea un socket per connettersi al server
        client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        client_socket.connect((server_ip, server_port))
        print(f"Sto provando a connettermi al server {server_ip}:{server_port}")

        while True:
            # Ricevi messaggio dal server
            server_message = client_socket.recv(1024).decode()
            print(server_message)

            # Interrompi il ciclo se il server chiude la connessione
            if not server_message:
                print("Connessione chiusa dal server.")
                break

            # Inserisci la scelta del tipo di scansione
            scelta = input("Inserisci la tua scelta: ").strip()
            client_socket.send(scelta.encode())

            # Ricevi la risposta dal server
            response = client_socket.recv(1024).decode()
            print(response)

            # Interrompi la comunicazione dopo una scansione
            if "Scansione registrata" in response or "Errore" in response:
                print("Chiudo la connessione.")
                break

        # Chiudi il socket
        client_socket.close()

    except socket.error as e:
        print(f"Errore nella connessione al server: {e}")
    except KeyboardInterrupt:
        print("\nConnessione interrotta manualmente.")
    finally:
        if client_socket:
            client_socket.close()

if __name__ == "__main__":
    # Controlla che siano forniti IP e porta
    if len(sys.argv) != 3:
        print("Uso corretto: python cli.py <server_ip> <server_port>")
        sys.exit(1)

    # Leggi l'IP e la porta dalla riga di comando
    server_ip = sys.argv[1]
    try:
        server_port = int(sys.argv[2])
    except ValueError:
        print("La porta deve essere un numero intero.")
        sys.exit(1)

    # Avvia il client
    start_client(server_ip, server_port)
