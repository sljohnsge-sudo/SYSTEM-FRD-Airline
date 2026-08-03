import mysql.connector

try:
    conn = mysql.connector.connect(
        host='127.0.0.1',
        user='root',
        password='',
        database='travel_booking_system'
    )
    cursor = conn.cursor()
    cursor.execute("ALTER TABLE service_fees ADD COLUMN amount_type ENUM('fixed', 'percentage') NOT NULL DEFAULT 'fixed'")
    conn.commit()
    print("Column amount_type added successfully.")
except Exception as e:
    print('Error:', e)
