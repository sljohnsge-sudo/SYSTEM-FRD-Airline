import mysql.connector
import json

def get_db_connection():
    return mysql.connector.connect(
        host="127.0.0.1",
        user="root",
        password="",
        database="travel_booking_system"
    )

def main():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM flights WHERE id = 140")
    print(json.dumps(cursor.fetchone(), default=str))
    cursor.close()
    conn.close()

if __name__ == '__main__':
    main()
