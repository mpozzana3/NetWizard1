import requests

def get_cidr():
    """Ottiene il CIDR dell'IP pubblico usando ipinfo.io."""
    try:
        response = requests.get("https://ipinfo.io/json", timeout=5)
        data = response.json()
        
        ip = data.get("ip")
        cidr = data.get("bogon")  # Verifica se è un IP privato (opzionale)
        netmask = data.get("netmask", "24")  # Default a /24 se mancante

        if ip and netmask:
            return f"{ip}/{netmask}"
        else:
            print("Errore: Subnet non disponibile")
            return None
    except requests.RequestException as e:
        print(f"Errore nel recupero del CIDR: {e}")
        return None

# Esempio di utilizzo
cidr = get_cidr()
if cidr:
    print(f"Subnet pubblica: {cidr}")
