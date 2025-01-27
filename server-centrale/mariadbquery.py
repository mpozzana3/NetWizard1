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
            for row in results:
                print(row)
        else:
            connection.commit()
            print(f"Query eseguita con successo. {cursor.rowcount} record interessati.")
    except mysql.connector.Error as err:
        print(f"Errore durante l'esecuzione della query: {err}")
    finally:
        cursor.close()

def main():
    """
    Entry point principale della CLI.
    """
    connection = connect_to_db()
    print("Connesso al database. Inserisci una query oppure digita 'exit' per uscire.")

    while True:
        query = input("SQL> ")
        if query.strip().lower() == "exit":
            print("Chiusura connessione al database. Arrivederci!")
            break
        execute_query(connection, query)

    connection.close()

if __name__ == "__main__":
    main()
