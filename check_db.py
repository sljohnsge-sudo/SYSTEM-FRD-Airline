import mysql.connector

conn = mysql.connector.connect(
    host="127.0.0.1",
    user="root",
    password="",
    database="travel_booking_system"
)
cursor = conn.cursor(dictionary=True)

print("--- b2c_bookings ---")
cursor.execute("SELECT * FROM b2c_bookings ORDER BY id DESC LIMIT 5")
for row in cursor.fetchall():
    print(row)

print("\n--- b2c_flight_bookings ---")
cursor.execute("SELECT * FROM b2c_flight_bookings ORDER BY id DESC LIMIT 5")
for row in cursor.fetchall():
    print(row)

print("\n--- b2c_hotel_bookings ---")
cursor.execute("SELECT * FROM b2c_hotel_bookings ORDER BY id DESC LIMIT 5")
for row in cursor.fetchall():
    print(row)

cursor.close()
conn.close()
