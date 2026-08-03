import mysql.connector

conn = mysql.connector.connect(
    host='127.0.0.1',
    user='root',
    password='',
    database='travel_booking_system'
)
cursor = conn.cursor()
cursor.execute("ALTER TABLE service_fees MODIFY transaction_type ENUM('issuance', 're-issue', 'refund', 'seat_map') NOT NULL")

# Insert default seat map fee if it doesn't exist
cursor.execute("SELECT * FROM service_fees WHERE transaction_type = 'seat_map'")
if not cursor.fetchone():
    cursor.execute("INSERT INTO service_fees (transaction_type, fee_type, amount) VALUES ('seat_map', 'markup', 0.00)")
conn.commit()
print("Success")
