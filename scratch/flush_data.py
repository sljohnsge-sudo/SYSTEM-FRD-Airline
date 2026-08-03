import mysql.connector

def get_db_connection():
    return mysql.connector.connect(
        host="127.0.0.1",
        user="root",
        password="",
        database="travel_booking_system"
    )

def flush_dummy_data():
    conn = get_db_connection()
    cursor = conn.cursor()
    
    tables_to_truncate = [
        "b2c_flight_bookings",
        "b2c_hotel_bookings",
        "b2c_bookings",
        "flight_bookings",
        "hotel_bookings",
        "bookings",
        "flights",
        "hotels",
        "agent_rewards",
        "b2c_payments",
        "wallet_transactions"
    ]
    
    try:
        cursor.execute("SET FOREIGN_KEY_CHECKS = 0;")
        for table in tables_to_truncate:
            try:
                cursor.execute(f"TRUNCATE TABLE {table};")
                print(f"Flushed table: {table}")
            except Exception as e:
                print(f"Error flushing {table}: {e}")
        cursor.execute("SET FOREIGN_KEY_CHECKS = 1;")
        conn.commit()
        print("All dummy data flushed successfully.")
    except Exception as e:
        print(f"Error: {e}")
    finally:
        cursor.close()
        conn.close()

if __name__ == "__main__":
    flush_dummy_data()
