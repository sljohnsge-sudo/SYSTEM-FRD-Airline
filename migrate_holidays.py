import mysql.connector

def run_migration():
    try:
        conn = mysql.connector.connect(
            host="127.0.0.1",
            user="root",
            password="",
            database="travel_booking_system"
        )
        cursor = conn.cursor()
        
        print("Migrating database for Holiday packages...")
        
        # 1. Update b2c_bookings table enum
        cursor.execute("ALTER TABLE b2c_bookings MODIFY COLUMN booking_type ENUM('flight', 'hotel', 'holiday') NOT NULL")
        print("Successfully updated booking_type enum in b2c_bookings table.")
        
        # 2. Create b2c_holiday_bookings table
        create_table_sql = """
        CREATE TABLE IF NOT EXISTS b2c_holiday_bookings (
            id INT AUTO_INCREMENT PRIMARY KEY,
            booking_id INT NOT NULL,
            package_name VARCHAR(100) NOT NULL,
            travel_date DATE NOT NULL,
            guests_count INT NOT NULL,
            include_flight BOOLEAN NOT NULL,
            guest_name VARCHAR(100) NOT NULL,
            email VARCHAR(100) NOT NULL,
            mobile VARCHAR(30) NOT NULL,
            special_requests TEXT DEFAULT NULL,
            original_price DECIMAL(12, 2) NOT NULL,
            service_fee DECIMAL(12, 2) DEFAULT 0.00,
            FOREIGN KEY (booking_id) REFERENCES b2c_bookings(id) ON DELETE CASCADE
        ) ENGINE=InnoDB;
        """
        cursor.execute(create_table_sql)
        print("Successfully created b2c_holiday_bookings table.")
        
        conn.commit()
        cursor.close()
        conn.close()
        print("Migration completed successfully!")
        
    except Exception as e:
        print(f"Error during migration: {e}")

if __name__ == "__main__":
    run_migration()
