import mysql.connector

try:
    conn = mysql.connector.connect(
        host='127.0.0.1',
        user='root',
        password='',
        database='travel_booking_system'
    )
    cursor = conn.cursor()
    cursor.execute("ALTER TABLE users ADD COLUMN status ENUM('active', 'inactive') NOT NULL DEFAULT 'active'")
    conn.commit()
    print("Column status added successfully.")
except Exception as e:
    print('Error:', e)
