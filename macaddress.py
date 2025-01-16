import requests

API_KEY = "at_XJNVC8kFlCjiTfa90leNXJmXq2Zai"

def get_mac_vendor(mac_address):
    """Recupera il vendor a partire dal MAC address usando l'API di macaddress.io."""
    url = f"https://api.macaddress.io/v1?apiKey={API_KEY}&output=json&search={mac_address}"
    try:
        response = requests.get(url)
        if response.status_code == 200:
            data = response.json()
            # Estrae il vendor dalla risposta dell'API
            if "vendorDetails" in data:
                return data["vendorDetails"]["companyName"]
            else:
                return "Vendor non trovato"
        else:
            return "Errore nella richiesta API"
    except Exception as e:
        return f"Errore: {e}"
