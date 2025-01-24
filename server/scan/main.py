import subprocess

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
    # Indirizzo IP o subnet da passare solo a scan-2.py
    target = "172.16.1.0/24"
    
    # Esegui gli script in ordine, passando la subnet solo a scan-2.py
    run_script("scan-1.py")
    run_script("scan-2.py", target)  # Passa la subnet solo a scan-2.py
    run_script("nmap.py")
    run_script("NetBios.py", target)
    run_script("enum4linux.py")
    run_script("smbclient.py")
    run_script("smbmap.py")

if __name__ == "__main__":
    main()
