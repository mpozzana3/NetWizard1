import subprocess
import sys
import re 

def subnet_extract():
    """Estrae la subnet dalla tabella di routing utilizzando il comando 'ip route'."""
    try:
        # Esegui il comando 'ip route'
        output = subprocess.check_output(["ip", "route"], text=True)
        
        # Cerca una riga con 'src' che contenga una subnet valida
        match = re.search(r"(\d+\.\d+\.\d+\.\d+/\d+)", output)
        if match:
            subnet = match.group(1)
            print(f"Subnet estratta: {subnet}")
            return subnet
        else:
            print("Nessuna subnet trovata nell'output.")
            return None
    except subprocess.CalledProcessError as e:
        print(f"Errore nell'esecuzione del comando 'ip route': {e}")
        return None
    except Exception as e:
        print(f"Errore generico: {e}")
        return None

def run_script(script_name, *args):
    """
    Esegue uno script Python esterno passando eventuali argomenti.
    Mostra solo un messaggio di completamento senza mostrare i risultati.
    """
    try:
        # Costruisci il comando per eseguire lo script
        command = ["python3", script_name] + list(args)
        
        # Esegui lo script
        result = subprocess.run(command, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        
        if result.returncode == 0:
            print(f"{script_name} completato con successo.")
        else:
            print(f"Errore nell'esecuzione di {script_name}.")
    except Exception as e:
        print(f"Errore nell'esecuzione di {script_name}: {e}")

def main():
    # Controlla se l'id_scansione è passato come argomento
    if len(sys.argv) < 2:
        print("Errore: Devi specificare un id_scansione come argomento.")
        sys.exit(1)
    
    # Ottieni l'id_scansione dagli argomenti
    id_scansione = sys.argv[1]
    
    # Indirizzo IP o subnet
    target = subnet_extract()
    
    # Esegui gli script in ordine, passando id_scansione e altri argomenti se necessario
    run_script("scan/scan-1.py", id_scansione)
    run_script("scan/scan-2.py", target, id_scansione)
    run_script("scan/nmap.py", id_scansione, target)
    run_script("scan/NetBios.py", target, id_scansione)
    run_script("scan/enum4linux.py", id_scansione)
    run_script("scan/smbclient.py", id_scansione)
    run_script("scan/smbmap.py", id_scansione)
    run_script("scan/masscan.py", id_scansione)


if __name__ == "__main__":
    main()

