import mysql.connector

try:
    conn = mysql.connector.connect(
        host='127.0.0.1',
        user='root',
        password='',
        database='travel_booking_system'
    )
    cursor = conn.cursor()
    cursor.execute("ALTER TABLE popups ADD COLUMN agent_id INT DEFAULT NULL")
    conn.commit()
    print("Column agent_id added to popups.")
except Exception as e:
    print('Error:', e)
