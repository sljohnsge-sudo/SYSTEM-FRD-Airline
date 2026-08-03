import mysql.connector

try:
    conn = mysql.connector.connect(
        host='127.0.0.1',
        user='root',
        password='',
        database='travel_booking_system'
    )
    cursor = conn.cursor()
    
    # Check if b2cadmin exists
    cursor.execute("SELECT id FROM users WHERE username = 'b2cadmin'")
    if not cursor.fetchone():
        cursor.execute("""
            INSERT INTO users (username, password, email, role, company_name, status)
            VALUES ('b2cadmin', 'b2cadmin123', 'b2cadmin@travel.com', 'b2c_admin', 'B2C Administration', 'active')
        """)
        conn.commit()
        print("b2cadmin created.")
    else:
        print("b2cadmin already exists.")
        
except Exception as e:
    print('Error:', e)
