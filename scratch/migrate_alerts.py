import mysql.connector
from check_db import get_db_connection

def migrate():
    conn = get_db_connection()
    if not conn:
        print("Failed to connect to database.")
        return

    cursor = conn.cursor()
    
    try:
        # Create b2c_price_alerts table if it doesn't exist
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS b2c_price_alerts (
                id INT AUTO_INCREMENT PRIMARY KEY,
                email VARCHAR(100) NOT NULL,
                mobile VARCHAR(30) NOT NULL,
                destination VARCHAR(100) NOT NULL,
                airline VARCHAR(100) DEFAULT 'Any Airline',
                notify_email BOOLEAN DEFAULT TRUE,
                notify_sms BOOLEAN DEFAULT FALSE,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            ) ENGINE=InnoDB;
        """)
        conn.commit()
        print("Successfully created b2c_price_alerts table!")
    except Exception as e:
        print(f"Error during migration: {e}")
    finally:
        cursor.close()
        conn.close()

if __name__ == "__main__":
    migrate()
