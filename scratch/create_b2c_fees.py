import mysql.connector

try:
    conn = mysql.connector.connect(
        host='127.0.0.1',
        user='root',
        password='',
        database='travel_booking_system'
    )
    cursor = conn.cursor()
    
    # Create b2c_service_fees table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS b2c_service_fees (
        id INT AUTO_INCREMENT PRIMARY KEY,
        transaction_type ENUM('flight_booking', 'hotel_booking', 'refund', 'cancellation', 're-issue', 'seat_map') NOT NULL,
        fee_type ENUM('fixed', 'percentage') NOT NULL,
        amount DECIMAL(10,2) NOT NULL DEFAULT 0.00,
        amount_type ENUM('fixed', 'percentage') NOT NULL DEFAULT 'fixed',
        updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
    )
    """)
    
    # Insert default configurations if table is empty
    cursor.execute("SELECT COUNT(*) FROM b2c_service_fees")
    count = cursor.fetchone()[0]
    if count == 0:
        cursor.execute("INSERT INTO b2c_service_fees (transaction_type, fee_type, amount, amount_type) VALUES ('flight_booking', 'fixed', 5.00, 'fixed')")
        cursor.execute("INSERT INTO b2c_service_fees (transaction_type, fee_type, amount, amount_type) VALUES ('hotel_booking', 'fixed', 10.00, 'fixed')")
        cursor.execute("INSERT INTO b2c_service_fees (transaction_type, fee_type, amount, amount_type) VALUES ('refund', 'fixed', 20.00, 'fixed')")
        cursor.execute("INSERT INTO b2c_service_fees (transaction_type, fee_type, amount, amount_type) VALUES ('cancellation', 'fixed', 25.00, 'fixed')")
        cursor.execute("INSERT INTO b2c_service_fees (transaction_type, fee_type, amount, amount_type) VALUES ('re-issue', 'fixed', 15.00, 'fixed')")
        cursor.execute("INSERT INTO b2c_service_fees (transaction_type, fee_type, amount, amount_type) VALUES ('seat_map', 'fixed', 0.00, 'fixed')")
        
    conn.commit()
    print("Database updated successfully.")
except Exception as e:
    print('Error:', e)
