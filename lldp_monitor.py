from scapy.all import *
import signal
import sys

# Funzione per terminare il programma
def signal_handler(sig, frame):
    print("Exiting...")
    sys.exit(0)

# Funzione per monitorare i pacchetti LLDP e ARP
def lldp_monitor(interface, verbose=True):
    signal.signal(signal.SIGINT, signal_handler)  # Gestione SIGINT

    # Filtro per pacchetti LLDP (0x88cc) e ARP
    def packet_callback(pkt):
        if pkt.haslayer(Ether):
            eth_type = pkt[Ether].type
            if eth_type == 0x88cc:
                print("LLDP packet:")
                print(pkt.show())  # Mostra informazioni dettagliate sul pacchetto LLDP
            elif eth_type == 0x0806:  # ARP
                print("ARP packet:")
                print(pkt.show())  # Mostra informazioni dettagliate sul pacchetto ARP
    
    # Avvia la cattura dei pacchetti sulla rete
    print(f"Monitoring packets on interface {interface}...")
    sniff(iface=interface, prn=packet_callback, store=0)

# Esegui il monitoraggio sulla tua interfaccia di rete (modifica l'interfaccia secondo necessità)
lldp_monitor("eth0", verbose=True)
