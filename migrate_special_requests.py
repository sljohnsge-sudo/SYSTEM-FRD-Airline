import mysql.connector

def run_migration():
    try:
        conn = mysql.connector.connect(
            host="localhost",
            user="root",
            password="",
            database="travel_booking_system"
        )
        cursor = conn.cursor()
        
        # New columns to add
        new_cols = [
            ("meal_preference", "VARCHAR(100) DEFAULT NULL"),
            ("wheelchair_assistance", "VARCHAR(100) DEFAULT NULL"),
            ("airport_assistance", "VARCHAR(100) DEFAULT NULL"),
            ("allergy_conditions", "VARCHAR(255) DEFAULT NULL"),
            ("other_requests", "TEXT DEFAULT NULL")
        ]
        
        for table in ["flight_bookings", "b2c_flight_bookings"]:
            print(f"Checking table: {table}")
            cursor.execute(f"DESCRIBE {table}")
            existing_cols = [row[0] for row in cursor.fetchall()]
            
            for col_name, col_type in new_cols:
                if col_name not in existing_cols:
                    print(f"Adding column {col_name} to {table}...")
                    cursor.execute(f"ALTER TABLE {table} ADD COLUMN {col_name} {col_type}")
                else:
                    print(f"Column {col_name} already exists in {table}.")
                    
        conn.commit()
        cursor.close()
        conn.close()
        print("Migration completed successfully!")
    except Exception as e:
        print(f"Migration error: {e}")

if __name__ == "__main__":
    run_migration()
