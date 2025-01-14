from scapy.all import *
import time

def host_scan(target_ip, ports, flags=['S'], protocols=['TCP', 'UDP'], iface="eth0", timeout=60):
    # Imposta il timeout
    timeout = len(ports) * 2 if 'UDP' in protocols else len(ports)
    
    # Inizia la scansione
    print(f"Scanning {target_ip}...")
    print(f"Using interface: {iface}")
    
    # Costruisci il pacchetto
    for protocol in protocols:
        for port in ports:
            if protocol == 'TCP':
                syn_packet = IP(dst=target_ip) / TCP(dport=port, flags=flags)
                response = sr1(syn_packet, timeout=timeout, iface=iface, verbose=0)
                if response:
                    if response.haslayer(TCP):
                        if response[TCP].flags == 18:  # SYN-ACK
                            print(f"Port {port} is open (TCP)")
                        elif response[TCP].flags == 20:  # RST
                            print(f"Port {port} is closed (TCP)")
            elif protocol == 'UDP':
                udp_packet = IP(dst=target_ip) / UDP(dport=port)
                response = sr1(udp_packet, timeout=timeout, iface=iface, verbose=0)
                if response:
                    print(f"Port {port} is open (UDP)")
                else:
                    print(f"Port {port} is closed (UDP)")

if __name__ == "__main__":
    host_scan("192.168.1.5", [80, 443], flags=["SYN"], protocols=["TCP", "UDP"], iface="eth0")
