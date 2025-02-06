import json

# Funzione per caricare il dizionario dei vendor dal file JSON
def load_vendor_data(json_file):
    try:
        with open(json_file, 'r') as file:
            vendor_data = json.load(file)
        return vendor_data
    except Exception as e:
        print(f"Errore nel caricamento del file JSON: {e}")
        return None

# Funzione per ottenere il vendor dal MAC address usando il dizionario caricato dal file JSON
def get_mac_vendor(mac_address, vendor_data):
    """Recupera il vendor a partire dal MAC address usando un dizionario offline caricato da un file JSON."""
    # Estrai i primi 6 caratteri del MAC address (1° e 2° ottetto)
    mac_prefix = mac_address[:8].upper()  # Assicurati che sia in maiuscolo per confrontare correttamente

    # Cerca nel dizionario
    for entry in vendor_data:
        if entry["macPrefix"].upper() == mac_prefix:
            return entry["vendorName"]
    
    return "Vendor non trovato"

# Carica i dati del vendor dal file JSON
vendor_data = load_vendor_data('mac-vendors-export.json')

if vendor_data:
    # Esempio di utilizzo
    mac_address = "00:0c:29:8d:46:02"
    vendor = get_mac_vendor(mac_address, vendor_data)
    print(f"MAC: {mac_address} - Vendor: {vendor}")

