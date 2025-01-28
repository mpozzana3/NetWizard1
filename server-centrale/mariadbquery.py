import mysql.connector
import sys

def connect_to_db():
    """
    Connette al database MariaDB locale.
    """
    try:
        connection = mysql.connector.connect(
            host="localhost",
            user="root",
            password="nuova_password",
            database="server_centrale",
            charset="utf8mb4",
            collation="utf8mb4_general_ci"
        )
        return connection
    except mysql.connector.Error as err:
        print(f"Errore di connessione al database: {err}")
        sys.exit(1)

def execute_query(connection, query):
    """
    Esegue una query sul database e restituisce i risultati.
    """
    cursor = connection.cursor()
    try:
        cursor.execute(query)
        if query.strip().lower().startswith("select"):
            results = cursor.fetchall()
            if results:
                print("Risultati della query:")
                for row in results:
                    print(row)
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
    Entry point principale della CLI. Legge la query dalla riga di comando.
    """
    if len(sys.argv) < 2:
        print("Errore: Devi fornire una query SQL come argomento.")
        sys.exit(1)

    query = sys.argv[1]  # La query è il primo argomento della riga di comando

    connection = connect_to_db()
    print("Connesso al database.")

    print(f"Eseguendo la query: {query}")
    execute_query(connection, query)

    connection.close()

if __name__ == "__main__":
    main()
