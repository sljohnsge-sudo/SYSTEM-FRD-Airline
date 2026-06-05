import mysql.connector

def get_db_connection():
    return mysql.connector.connect(
        host="127.0.0.1",
        user="root",
        password="",
        database="travel_booking_system"
    )

conn = get_db_connection()
cursor = conn.cursor(dictionary=True)
cursor.execute("SELECT id, location FROM hotels")
hotels = cursor.fetchall()

for h in hotels:
    loc_lower = h['location'].lower()
    img_url = ""
    if 'london' in loc_lower or 'uk' in loc_lower or 'lhr' in loc_lower:
        img_url = 'hotel_london.jpg'
    elif 'dubai' in loc_lower or 'uae' in loc_lower or 'dxb' in loc_lower:
        img_url = 'hotel_dubai.jpg'
    elif 'maldives' in loc_lower or 'mle' in loc_lower:
        img_url = 'hotel_maldives.jpg'
    elif 'singapore' in loc_lower or 'sin' in loc_lower:
        img_url = 'hotel_singapore.jpg'
    
    if img_url:
        cursor.execute("UPDATE hotels SET image_url = %s WHERE id = %s", (img_url, h['id']))

conn.commit()
cursor.close()
conn.close()
print("Updated hotel images in the DB successfully.")
