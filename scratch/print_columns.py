import mysql.connector

def get_db_connection():
    return mysql.connector.connect(
        host="127.0.0.1",
        user="root",
        password="",
        database="travel_booking_system"
    )

def print_table_columns(table_name):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(f"DESCRIBE {table_name}")
    print(f"\n--- Columns in {table_name} ---")
    for row in cursor.fetchall():
        print(f"{row[0]} ({row[1]})")
    cursor.close()
    conn.close()

def main():
    print_table_columns("flight_bookings")
    print_table_columns("b2c_flight_bookings")
    print_table_columns("bookings")
    print_table_columns("b2c_bookings")
    print_table_columns("flights")
    print_table_columns("users")
    print_table_columns("b2c_users")

if __name__ == '__main__':
    main()
