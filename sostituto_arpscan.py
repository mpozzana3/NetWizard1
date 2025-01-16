from scapy.all import ARP, Ether, srp
import sys
from mac_vendor_lookup import MacLookup

# File per salvare i risultati
output_file = "test_attività.txt"

def get_mac_vendor(mac_address):
    """Recupera il vendor a partire dal MAC address."""
    try:
        vendor = MacLookup().lookup(mac_address)
        return vendor
    except Exception as e:
        return f"Errore: {e}"

def arp_scan(target_ip_range):
    """Esegui una scansione ARP su un intervallo di IP."""
    # Costruisci il pacchetto ARP per la richiesta
    arp_request = ARP(pdst=target_ip_range)
    broadcast = Ether(dst="ff:ff:ff:ff:ff:ff")
    # Combina il pacchetto ARP con il broadcast Ethernet
    arp_request_broadcast = broadcast/arp_request

    # Sovrascrive il file all'inizio della scansione
    with open(output_file, "w") as f:
        f.write(f"Risultati della scansione ARP su {target_ip_range}:\n")

    # Invia la richiesta e ricevi le risposte
    print(f"Scansione ARP in corso su {target_ip_range}...")
    answered_list = srp(arp_request_broadcast, timeout=2, verbose=False)[0]

    # Elenco per i dispositivi rilevati
    devices = []

    for element in answered_list:
        ip = element[1].psrc
        mac = element[1].hwsrc
        vendor = get_mac_vendor(mac)
        devices.append((ip, mac, vendor))
        
        # Mostra i risultati e scrivili nel file
        print(f"IP: {ip} - MAC: {mac} - Vendor: {vendor}")
        with open(output_file, "a") as f:
            f.write(f"IP: {ip} - MAC: {mac} - Vendor: {vendor}\n")

    return devices

def main():
    if len(sys.argv) < 2:
        print("Uso: python3 arp_scan.py <ip_range>")
        sys.exit(1)

    target_ip_range = sys.argv[1]
    devices = arp_scan(target_ip_range)

    if not devices:
        print("Nessun dispositivo trovato.")
    else:
        print(f"\nDispositivi trovati: {len(devices)}")
        for ip, mac, vendor in devices:
            print(f"IP: {ip} - MAC: {mac} - Vendor: {vendor}")

if __name__ == "__main__":
    main()

