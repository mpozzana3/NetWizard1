import argparse
import requests

SERVER_URL = "http://127.0.0.1:5000"  # URL del server

def send_command(command, args):
    """Invia un comando al server."""
    try:
        response = requests.post(f"{SERVER_URL}/execute", json={"command": command, "args": args})
        if response.status_code == 200:
            print(f"Risultato: {response.json()['result']}")
        else:
            print(f"Errore dal server: {response.text}")
    except requests.RequestException as e:
        print(f"Errore di connessione: {e}")

def main():
    parser = argparse.ArgumentParser(description="CLI per comunicare con il server remoto")
    parser.add_argument("command", type=str, help="Il comando da eseguire")
    parser.add_argument("args", nargs="*", help="Argomenti del comando")
    
    args = parser.parse_args()
    send_command(args.command, args.args)

if __name__ == "__main__":
    main()
