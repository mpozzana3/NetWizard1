import mysql.connector
import sys
import json

# Carica la configurazione da file JSON
with open('config2.json', 'r') as f:
    config = json.load(f)

# Parametri DB MariaDB
DB_HOST = config['database']['db_host']
DB_USER = config['database']['db_user']
DB_PASSWORD = config['database']['db_password']
DB_NAME = config['database']['db_name']

def connect_to_db():
    """
    Connette al database MariaDB locale.
    """
    try:
        connection = mysql.connector.connect(
            host=DB_HOST,
            user=DB_USER,
            password=DB_PASSWORD,
            database=DB_NAME,
            charset="utf8mb4",
            collation="utf8mb4_general_ci"
        )
        return connection
    except mysql.connector.Error as err:
        print(f"Errore di connessione al database: {err}")
        sys.exit(1)

def execute_query(connection, query):
    """
    Esegue una query sul database e restituisce i risultati con un separatore personalizzato.
    """
    cursor = connection.cursor()
    try:
        cursor.execute(query)
        if query.strip().lower().startswith("select"):
            results = cursor.fetchall()
            column_names = [desc[0] for desc in cursor.description]  # Ottieni i nomi delle colonne

            if results:
              #  print("Risultati della query:")
              #  print(" § ".join(column_names))  # Stampa l'intestazione delle colonne
              #  print("-" * 40)

                for row in results:
                    print(" § ".join(str(cell) for cell in row)) 
            else:
                print("Nessun risultato trovato.")
        else:
            connection.commit()
            print(f"Query eseguita con successo. {cursor.rowcount} record interessati.")
    except mysql.connector.Error as err:
        print(f"Errore durante l'esecuzione della query: {err}")
    finally:
        cursor.close()

def main():
    """
    Entry point principale. Legge la query dalla riga di comando.
    """
    if len(sys.argv) < 2:
        print("Errore: Devi fornire una query SQL come argomento.")
        sys.exit(1)

    query = sys.argv[1]  

    connection = connect_to_db()
    # print("Connesso al database.")

    # print(f"Eseguendo la query: {query}")
    execute_query(connection, query)

    connection.close()

if __name__ == "__main__":
    main()
