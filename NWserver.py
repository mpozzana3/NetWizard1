import socket
import ssl
import os
import time
import logging
from OpenSSL import crypto

class NWServer:
    def __init__(self, port, timeout, verbose):
        self.port = port          # La porta su cui il server ascolta
        self.timeout = timeout    # Timeout in secondi
        self.verbose = verbose    # Flag di verbosità
        self.connections = []     # Lista delle connessioni dei client
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

    def get_socket(self):
        # Seleziona se ci sono attività sul server o sulle connessioni
        readable, _, errored = select.select([self.server_socket] + self.connections, [], self.connections, self.timeout)

        # Gestione degli errori delle connessioni
        for sock in errored:
            sock.close()
            self.connections.remove(sock)
            logging.error(f"Socket {sock.getpeername()} ha avuto un errore")

        # Accetta nuove connessioni
        for sock in readable:
            if sock is self.server_socket:
                client_socket, client_address = self.server_socket.accept()
                self.connections.append(client_socket)
                if self.verbose:
                    logging.info(f"Nuova connessione in arrivo da {client_address}")
                return client_socket

        # Gestisci le connessioni esistenti
        for sock in readable:
            if sock is not self.server_socket:
                if sock.recv(1, socket.MSG_PEEK) == b'':  # Client chiuso la connessione
                    self.connections.remove(sock)
                    sock.close()
                    if self.verbose:
                        logging.info(f"Connessione chiusa dal client {sock.getpeername()}")
                    continue
                if self.verbose:
                    logging.info(f"Messaggio in arrivo da {sock.getpeername()}")
                return sock

        return None  # Nessun messaggio arrivato

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

if __name__ == '__main__':
    logging.basicConfig(level=logging.DEBUG)  # Imposta il logging a livello DEBUG per verbosità

    # Crea una nuova istanza del server
    server = NWServer(port=12345, timeout=5, verbose=True)
    server.initssl()  # Inizializza SSL

    ssl_server = server.start_ssl_server()  # Avvia il server SSL

    while True:
        # Gestisci le connessioni dei client
        client_socket = server.get_socket()

        if client_socket:
            # Leggi i dati dal client
            data = client_socket.recv(1024)
            if data:
                logging.info(f"Messaggio ricevuto: {data.decode()}")
            client_socket.close()
