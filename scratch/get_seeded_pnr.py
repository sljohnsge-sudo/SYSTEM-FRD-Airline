import mysql.connector

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
    cursor.execute("SELECT pnr_reference, passenger_name, ticket_status FROM flight_bookings LIMIT 5")
    rows = cursor.fetchall()
    print("Seeded Flight Bookings:")
    for row in rows:
        print(f"PNR: {row['pnr_reference']}, Passenger: {row['passenger_name']}, Status: {row['ticket_status']}")
    cursor.close()
    conn.close()

if __name__ == '__main__':
    main()
