# NetWizard - Scansione Remota delle Reti

Questo progetto è stato realizzato con l'intento di raccogliere le principali tecniche di scansione delle vulnerabilità di una rete e permettere di effettuarle anche da remoto, senza la necessità di collegarsi direttamente alla rete.

## Struttura del Progetto
Il progetto è suddiviso in tre componenti principali:

- **`server/`**: Deve essere scaricata sul server della rete che si desidera scansionare. Contiene tutti i codici necessari per eseguire le scansioni.
- **`server-centrale/`**: Deve risiedere sul server in cui è presente il database che memorizza tutte le scansioni su tutte le reti (utile se si vuole installare `server/` su diverse reti).
- **`scanner_gui/`**: Contiene gli script necessari per avviare le scansioni.

---

## Preparazione del Progetto

### 1. Installazione del Database
Il progetto richiede un RDBMS. 
Il database supportato è **MariaDB**.

Dopo aver installato MariaDB, modificare il file **`server/aggiornadb.py`** inserendo i dati di accesso ai due database.

### 2. Configurazione del Database Centrale
Sul database del **server centrale**, popolare la tabella `azienda` con le informazioni relative alla rete in cui è presente la cartella `server/`. 

#### Esempio di query SQL:
```sql
INSERT INTO azienda (azienda, p_iva, IP_sonda, Porta_sonda) 
VALUES ('Nome Azienda', 'Partita IVA', 'Indirizzo IP', 'Numero Porta');
```

### 3. Configurazione dei Client di Scansione
Nei file `cli.py`, `scansioni.py` e `analisi.py`, aggiornare le informazioni di connessione al **server centrale**.

Se, ad esempio, il **server-centrale** riporta il messaggio:
```
Server in ascolto su 170.0.1.:5500
```
Dovremo modificare i file `cli.py`, `scansioni.py` e `analisi.py` come segue:

```python
SERVER_HOST = "170.0.1"
SERVER_PORT = 5500
```

---

## Utilizzo del Progetto

### 1. Avvio dei Server
Assicurarsi che entrambi i server (`server/` e `server-centrale/`) siano in esecuzione.

### 2. Esecuzione delle Scansioni
Le scansioni possono essere avviate in due modi:

- **Da terminale**:
  ```bash
  python3 cli.py
  ```
- **Tramite interfaccia web**:
  ```bash
  python3 scansioni.py
  ```

### 3. Analisi dei Risultati
I risultati possono essere analizzati:

- **Da terminale**:
  ```bash
  python3 cli.py
  ```
- **Tramite interfaccia web**:
  ```bash
  python3 analisi.py
  ```

---

## Requisiti
- Python 3.x
- MariaDB
- Dipendenze Python elencate in `requirements.txt` (installabili con `pip install -r requirements.txt`)

---

## Autore
Progetto sviluppato da **Matteo Pozz**.

