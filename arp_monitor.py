import scapy.all as scapy
import json
import signal
import sys

class ArpMonitor:
    def __init__(self, interface, verb=1, count=0):
        self.interface = interface
        self.verb = verb
        self.count = int(count)
        self.pairs = {"module": "Arp_Monitor", "data": {}}

    def packet_callback(self, pkt):
        if pkt.haslayer(scapy.ARP):
            arp_pkt = pkt[scapy.ARP]
            saddr_ip = arp_pkt.psrc
            saddr_mac = arp_pkt.hwsrc

            if saddr_ip in self.pairs["data"]:
                if self.pairs["data"][saddr_ip] != saddr_mac:
                    print(f"ARP SPOOFING DETECTED: {saddr_ip}")
            else:
                self.pairs["data"][saddr_ip] = saddr_mac

            packet_info = [
                saddr_ip, saddr_mac, arp_pkt.pdst, arp_pkt.hwdst,
                arp_pkt.hwlen, arp_pkt.proto, arp_pkt.protodst
            ]

            if self.verb == 0:
                print(f"{saddr_ip: <15} {saddr_mac: <17} -> {arp_pkt.pdst: <15} {arp_pkt.hwdst: <17}")
            elif self.verb != "silent":
                print("---------------------------------------")
                print(packet_info)

            self.count -= 1
            if self.count == 0:
                return True
        return False

    def start(self):
        print(f"Starting ARP monitor on {self.interface}")
        sniff_result = scapy.sniff(
            iface=self.interface, filter="arp", prn=self.packet_callback,
            stop_filter=self.packet_callback if self.count > 0 else None
        )
        return json.dumps(self.pairs)

def signal_handler(sig, frame):
    print("Exiting...")
    sys.exit(0)

if __name__ == "__main__":
    signal.signal(signal.SIGINT, signal_handler)

    interface = "eth0"  # Change to your desired interface
    monitor = ArpMonitor(interface, verb=1, count=10)  # Adjust verb and count as needed
    result = monitor.start()
    print(result)
# La funzione arp_monitor cattura pacchetti ARP e memorizza gli indirizzi IP-MAC in un dizionario. Se un indirizzo IP è associato a un MAC diverso, viene segnalato un possibile ARP spoofing. 
# A seconda del livello di verbosità (verb), stampa informazioni dettagliate sui pacchetti ARP. 
# Può essere configurato per fermarsi dopo un numero definito di pacchetti (count).
