# script per lanciare tutte le scansioni in sequenza
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
    Se uno script fallisce, interrompe l'esecuzione.
    """
    try:
        command = ["python3", script_name] + list(args)
        print(f"Lancio {script_name}...")        

        result = subprocess.run(command, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)

        print(f"{script_name} completato con successo.")
    
    except subprocess.CalledProcessError:
        print(f"❌ Errore: {script_name} fallito. Interruzione delle scansioni.")
        sys.exit(1)  # Termina lo script principale
    
    except Exception as e:
        print(f"❌ Errore generico in {script_name}: {e}")
        sys.exit(1)

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

