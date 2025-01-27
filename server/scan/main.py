import subprocess
import sys

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
    
    # Indirizzo IP o subnet da passare solo a scan-2.py
    target = "172.16.1.0/24"
    
    # Esegui gli script in ordine, passando id_scansione e altri argomenti se necessario
    run_script("scan/scan-1.py", id_scansione)
    run_script("scan/scan-2.py", target, id_scansione)  # Passa anche la subnet a scan-2.py
    run_script("scan/nmap.py", id_scansione)
    run_script("scan/NetBios.py", target, id_scansione)
    run_script("scan/enum4linux.py", id_scansione)
    run_script("scan/smbclient.py", id_scansione)
    run_script("scan/smbmap.py", id_scansione)

if __name__ == "__main__":
    main()

