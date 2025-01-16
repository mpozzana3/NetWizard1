import socket
import ssl
import os
import threading
import logging
from OpenSSL import crypto
import shellwords

class NWServer:
    def __init__(self, port, timeout, verbose):
        self.port = int(port)           # La porta su cui il server ascolta
        self.timeout = int(timeout)     # Timeout in secondi
        self.verbose = bool(verbose)   # Flag di verbosità
        self.server_socket = None

        # Creazione del server TCP
        try:
            self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.server_socket.bind(('0.0.0.0', self.port))
            self.server_socket.listen(5)
            self.server_socket.setblocking(0)
        except socket.error as ex:
            raise Exception(f"Impossibile inizializzare il server per la porta {self.port}: {ex}")

    def get_server_socket(self):
        return self.server_socket

    def initssl(self):
        cert_dir = os.path.join(os.getcwd(), 'certs')

        # Crea una cartella per i certificati se non esiste
        if not os.path.exists(cert_dir):
            os.makedirs(cert_dir)

        # Controlla se esistono già i certificati, altrimenti creali
        if not os.path.isfile(os.path.join(cert_dir, 'server_private.pem')):
            # Genera una nuova chiave privata e pubblica
            key = crypto.PKey()
            key.generate_key(crypto.TYPE_RSA, 2048)

            with open(os.path.join(cert_dir, 'server_private.pem'), 'wb') as key_file:
                key_file.write(crypto.dump_privatekey(crypto.FILETYPE_PEM, key))

            with open(os.path.join(cert_dir, 'server_public.pem'), 'wb') as key_file:
                key_file.write(crypto.dump_publickey(crypto.FILETYPE_PEM, key))

            # Crea un certificato autofirmato
            cert = crypto.X509()
            cert.set_version(2)
            cert.set_serial_number(0)
            cert.gmtime_adj_notBefore(0)
            cert.gmtime_adj_notAfter(3600)
            cert.set_pubkey(key)
            cert.set_subject(crypto.X509Name([
                ('CN', 'nwserver'),
                ('DC', 'nwserver')
            ]))
            cert.set_issuer(cert.get_subject())
            cert.sign(key, 'sha1')

            with open(os.path.join(cert_dir, 'certificate.pem'), 'wb') as cert_file:
                cert_file.write(crypto.dump_certificate(crypto.FILETYPE_PEM, cert))

    def start_ssl_server(self):
        # Aggiungi la capacità SSL al socket del server
        context = ssl.create_default_context(ssl.Purpose.CLIENT_AUTH)
        context.load_cert_chain(certfile=os.path.join(os.getcwd(), 'certs/certificate.pem'),
                                keyfile=os.path.join(os.getcwd(), 'certs/server_private.pem'))
        
        ssl_socket = context.wrap_socket(self.server_socket, server_side=True)
        return ssl_socket


def server(command):
    if command == "start":
        print("Starting server")
        nwserver = NWServer(port='2000', timeout='60', verbose='1')
        nwserver.initssl()  # Inizializza SSL

        ssl_server = nwserver.start_ssl_server()  # Avvia il server SSL
        print("OK")

        def handle_connection(connection):
            try:
                connection.sendall(str.encode(str($stdout)))
                while True:
                    line_in = connection.recv(1024).decode()
                    if not line_in:
                        break
                    line_in = line_in.strip()
                    print("=>", line_in)
                    program, *arguments = shellwords.split(line_in)
                    if builtin(program):
                        # Builtins return a value
                        ret = call_builtin(program, *arguments)
                        connection.sendall(str.encode(ret))
                connection.close()
            except Exception as e:
                print("Error:", e)

        # Gestisci le connessioni in un nuovo thread
        while True:
            connection, client_address = ssl_server.accept()
            print(f"Connection from {client_address}")
            th = threading.Thread(target=handle_connection, args=(connection,))
            th.start()

    elif command == "initssl":
        nwserver = NWServer(port='2000', timeout='60', verbose='0')
        nwserver.initssl()

    print(f"COMMAND: {command}")

# Funzione per emulare il comportamento "trap" di Ruby
import signal
def trap_signal():
    signal.signal(signal.SIGINT, lambda signum, frame: print("Exiting..."))
    signal.pause()  # Aspetta il segnale SIGINT

if __name__ == "__main__":
    # Esegui il server con il comando "start" o "initssl"
    server("start")
    trap_signal()
