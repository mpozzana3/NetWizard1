import subprocess
import re

def get_ips_from_file(filename):
    """
    Legge il file e restituisce una lista di IP.
    """
    ips = []
    with open(filename, 'r') as file:
        lines = file.readlines()
        for line in lines:
            # Estrai solo gli IP dalle righe che contengono l'indirizzo IP
            match = re.match(r"(\d+\.\d+\.\d+\.\d+)", line)
            if match:
                ips.append(match.group(1))
    return ips

def run_smbclient_scan(ip):
    """
    Esegue il comando smbclient -L su un IP e restituisce l'output.
    """
    try:
        # Usa -N per il login anonimo (senza password)
        result = subprocess.run(['smbclient', '-L', f'\\\\{ip}', '-N'], capture_output=True, text=True, timeout=60)
        if result.returncode == 0:
            return result.stdout
        else:
            return f"session setup failed: {result.stderr.strip()}"
    except subprocess.TimeoutExpired:
        return f"session setup failed: timed out after 60 seconds"
    except Exception as e:
        return f"session setup failed: {str(e)}"

def save_output(results, output_filename):
    """
    Salva i risultati in un file di testo nel formato richiesto.
    """
    with open(output_filename, 'w') as file:
        for ip, output in results.items():
            file.write(f"Risultato per IP: {ip}\n")
            file.write(f"{output}\n")
            file.write("\n" + "="*50 + "\n")

def main(input_file, output_file):
    """
    Funzione principale che esegue la scansione SMB per ogni IP e salva i risultati.
    """
    ips = get_ips_from_file(input_file)
    results = {}
    
    for ip in ips:
        print(f"Scansionando {ip}...")
        output = run_smbclient_scan(ip)
        results[ip] = output
    
    save_output(results, output_file)
    print(f"Scansione completata. I risultati sono stati salvati in {output_file}")

# Specifica il file di input e il file di output
input_file = 'nbtscan.txt'
output_file = 'testsmbc.txt'

# Esegui lo script
main(input_file, output_file)

