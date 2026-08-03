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
    
    pnr_code = 'PNR308417'
    
    print("--- Searching B2B flight_bookings ---")
    cursor.execute("""
        SELECT fb.*, f.flight_number, f.airline, f.origin, f.destination, f.departure_time, f.arrival_time, f.flight_type, f.gds_source,
               b.invoice_number, b.created_at, b.status AS booking_status, b.total_price
        FROM flight_bookings fb
        JOIN flights f ON fb.flight_id = f.id
        JOIN bookings b ON fb.booking_id = b.id
        WHERE fb.pnr_reference = %s
    """, (pnr_code,))
    b2b = cursor.fetchall()
    print(json.dumps(b2b, default=str, indent=2))
    
    print("\n--- Searching B2C b2c_flight_bookings ---")
    cursor.execute("""
        SELECT fb.*, f.flight_number, f.airline, f.origin, f.destination, f.departure_time, f.arrival_time, f.flight_type, f.gds_source,
               b.invoice_number, b.created_at, b.status AS booking_status, b.total_price
        FROM b2c_flight_bookings fb
        JOIN flights f ON fb.flight_id = f.id
        JOIN b2c_bookings b ON fb.booking_id = b.id
        WHERE fb.pnr_reference = %s
    """, (pnr_code,))
    b2c = cursor.fetchall()
    print(json.dumps(b2c, default=str, indent=2))
    
    cursor.close()
    conn.close()

if __name__ == '__main__':
    main()
