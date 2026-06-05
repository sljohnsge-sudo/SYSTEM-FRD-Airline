import mysql.connector
import datetime
import random
from decimal import Decimal

def initialize_database():
    try:
        # Establish connection to MariaDB server
        conn = mysql.connector.connect(
            host="127.0.0.1",
            user="root",
            password=""
        )
        cursor = conn.cursor()
        
        # Create database
        cursor.execute("CREATE DATABASE IF NOT EXISTS travel_booking_system CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci")
        print("Database 'travel_booking_system' created or verified.")
        
        # Connect to the database
        cursor.execute("USE travel_booking_system")
        
        # Disable foreign key checks to drop tables
        cursor.execute("SET FOREIGN_KEY_CHECKS = 0")
        
        tables_to_drop = [
            "agent_rewards", "timatic_checks", "service_fees", "support_tickets",
            "hotel_bookings", "b2c_hotel_bookings", "b2c_holiday_bookings", "flight_bookings", "b2c_flight_bookings", "b2c_bookings", "bookings", "rooms", "hotels",
            "flights", "b2c_users", "users", "popups"
        ]
        for table in tables_to_drop:
            cursor.execute(f"DROP TABLE IF EXISTS {table}")
            print(f"Dropped table if exists: {table}")
            
        cursor.execute("SET FOREIGN_KEY_CHECKS = 1")
        
        # Define table schemas
        table_schemas = {
            "b2c_users": """
                CREATE TABLE b2c_users (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    email VARCHAR(100) UNIQUE NOT NULL,
                    password VARCHAR(255) NOT NULL,
                    full_name VARCHAR(100) NOT NULL,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                ) ENGINE=InnoDB;
            """,
            "users": """
                CREATE TABLE users (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    username VARCHAR(50) UNIQUE NOT NULL,
                    password VARCHAR(255) NOT NULL,
                    email VARCHAR(100) NOT NULL,
                    role ENUM('agent', 'admin') NOT NULL,
                    credit_balance DECIMAL(15, 2) DEFAULT 0.00,
                    company_name VARCHAR(100),
                    phone VARCHAR(20),
                    onboarded_at DATETIME DEFAULT CURRENT_TIMESTAMP
                ) ENGINE=InnoDB;
            """,
            "flights": """
                CREATE TABLE flights (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    flight_number VARCHAR(10) UNIQUE NOT NULL,
                    airline VARCHAR(50) NOT NULL,
                    origin VARCHAR(50) NOT NULL,
                    destination VARCHAR(50) NOT NULL,
                    departure_time DATETIME NOT NULL,
                    arrival_time DATETIME NOT NULL,
                    price DECIMAL(10, 2) NOT NULL,
                    seats_available INT NOT NULL,
                    flight_type ENUM('LCC', 'NDC', 'GDS') NOT NULL,
                    gds_source VARCHAR(20) DEFAULT 'GDS',
                    segment_count INT DEFAULT 1
                ) ENGINE=InnoDB;
            """,
            "hotels": """
                CREATE TABLE hotels (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    name VARCHAR(100) NOT NULL,
                    location VARCHAR(100) NOT NULL,
                    rating INT DEFAULT 3,
                    description TEXT,
                    image_url VARCHAR(255)
                ) ENGINE=InnoDB;
            """,
            "rooms": """
                CREATE TABLE rooms (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    hotel_id INT NOT NULL,
                    room_type VARCHAR(50) NOT NULL,
                    price_per_night DECIMAL(10, 2) NOT NULL,
                    availability BOOLEAN DEFAULT TRUE,
                    FOREIGN KEY (hotel_id) REFERENCES hotels(id) ON DELETE CASCADE
                ) ENGINE=InnoDB;
            """,
            "bookings": """
                CREATE TABLE bookings (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    agent_id INT NOT NULL,
                    booking_type ENUM('flight', 'hotel') NOT NULL,
                    status ENUM('ticketed', 'non-ticketed', 'refunded', 'voided') DEFAULT 'non-ticketed',
                    total_price DECIMAL(12, 2) NOT NULL,
                    invoice_number VARCHAR(50) UNIQUE NOT NULL,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (agent_id) REFERENCES users(id) ON DELETE CASCADE
                ) ENGINE=InnoDB;
            """,
            "flight_bookings": """
                CREATE TABLE flight_bookings (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    booking_id INT NOT NULL,
                    flight_id INT NOT NULL,
                    passenger_name VARCHAR(100) NOT NULL,
                    seat_number VARCHAR(10),
                    gds_type ENUM('Amadeus', 'Sabre', 'LCC', 'NDC', 'GDS') NOT NULL,
                    ticket_status ENUM('ticketed', 'non-ticketed', 'refunded', 'voided') NOT NULL,
                    original_price DECIMAL(10, 2) NOT NULL,
                    service_fee DECIMAL(10, 2) DEFAULT 0.00,
                    pnr_reference VARCHAR(20) DEFAULT NULL,
                    ticket_number VARCHAR(30) DEFAULT NULL,
                    passport_number VARCHAR(50) DEFAULT NULL,
                    mobile VARCHAR(30) DEFAULT NULL,
                    email VARCHAR(100) DEFAULT NULL,
                    FOREIGN KEY (booking_id) REFERENCES bookings(id) ON DELETE CASCADE,
                    FOREIGN KEY (flight_id) REFERENCES flights(id) ON DELETE CASCADE
                ) ENGINE=InnoDB;
            """,
            "b2c_bookings": """
                CREATE TABLE b2c_bookings (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    b2c_user_id INT DEFAULT NULL,
                    booking_type ENUM('flight', 'hotel', 'holiday') NOT NULL,
                    status VARCHAR(50) DEFAULT 'non-ticketed',
                    total_price DECIMAL(12, 2) NOT NULL,
                    invoice_number VARCHAR(50) UNIQUE NOT NULL,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                ) ENGINE=InnoDB;
            """,
            "b2c_flight_bookings": """
                CREATE TABLE b2c_flight_bookings (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    booking_id INT NOT NULL,
                    flight_id INT NOT NULL,
                    passenger_name VARCHAR(100) NOT NULL,
                    seat_number VARCHAR(10),
                    gds_type VARCHAR(50) NOT NULL,
                    ticket_status VARCHAR(50) NOT NULL,
                    original_price DECIMAL(10, 2) NOT NULL,
                    service_fee DECIMAL(10, 2) DEFAULT 0.00,
                    pnr_reference VARCHAR(20) DEFAULT NULL,
                    ticket_number VARCHAR(30) DEFAULT NULL,
                    passport_number VARCHAR(50) DEFAULT NULL,
                    mobile VARCHAR(30) DEFAULT NULL,
                    email VARCHAR(100) DEFAULT NULL,
                    meal_preference VARCHAR(100) DEFAULT NULL,
                    wheelchair_assistance VARCHAR(100) DEFAULT NULL,
                    airport_assistance VARCHAR(100) DEFAULT NULL,
                    allergy_conditions VARCHAR(255) DEFAULT NULL,
                    other_requests TEXT DEFAULT NULL,
                    FOREIGN KEY (booking_id) REFERENCES b2c_bookings(id) ON DELETE CASCADE,
                    FOREIGN KEY (flight_id) REFERENCES flights(id) ON DELETE CASCADE
                ) ENGINE=InnoDB;
            """,
            "b2c_hotel_bookings": """
                CREATE TABLE b2c_hotel_bookings (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    booking_id INT NOT NULL,
                    room_id INT NOT NULL,
                    check_in DATE NOT NULL,
                    check_out DATE NOT NULL,
                    guest_name VARCHAR(100) NOT NULL,
                    email VARCHAR(100) NOT NULL,
                    mobile VARCHAR(30) NOT NULL,
                    original_price DECIMAL(10, 2) NOT NULL,
                    service_fee DECIMAL(10, 2) DEFAULT 0.00,
                    FOREIGN KEY (booking_id) REFERENCES b2c_bookings(id) ON DELETE CASCADE,
                    FOREIGN KEY (room_id) REFERENCES rooms(id) ON DELETE CASCADE
                ) ENGINE=InnoDB;
            """,
            "b2c_holiday_bookings": """
                CREATE TABLE b2c_holiday_bookings (
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
            """,
            "b2c_price_alerts": """
                CREATE TABLE b2c_price_alerts (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    email VARCHAR(100) NOT NULL,
                    mobile VARCHAR(30) NOT NULL,
                    destination VARCHAR(100) NOT NULL,
                    airline VARCHAR(100) DEFAULT 'Any Airline',
                    notify_email BOOLEAN DEFAULT TRUE,
                    notify_sms BOOLEAN DEFAULT FALSE,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                ) ENGINE=InnoDB;
            """,
            "hotel_bookings": """
                CREATE TABLE hotel_bookings (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    booking_id INT NOT NULL,
                    room_id INT NOT NULL,
                    check_in DATE NOT NULL,
                    check_out DATE NOT NULL,
                    guest_name VARCHAR(100) NOT NULL,
                    original_price DECIMAL(10, 2) NOT NULL,
                    service_fee DECIMAL(10, 2) DEFAULT 0.00,
                    FOREIGN KEY (booking_id) REFERENCES bookings(id) ON DELETE CASCADE,
                    FOREIGN KEY (room_id) REFERENCES rooms(id) ON DELETE CASCADE
                ) ENGINE=InnoDB;
            """,
            "support_tickets": """
                CREATE TABLE support_tickets (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    agent_id INT NOT NULL,
                    subject VARCHAR(100) NOT NULL,
                    message TEXT NOT NULL,
                    status ENUM('open', 'resolved') DEFAULT 'open',
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (agent_id) REFERENCES users(id) ON DELETE CASCADE
                ) ENGINE=InnoDB;
            """,
            "service_fees": """
                CREATE TABLE service_fees (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    transaction_type ENUM('issuance', 're-issue', 'refund') NOT NULL,
                    fee_type ENUM('markup', 'markdown') NOT NULL,
                    amount DECIMAL(10, 2) NOT NULL
                ) ENGINE=InnoDB;
            """,
            "timatic_checks": """
                CREATE TABLE timatic_checks (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    agent_id INT NOT NULL,
                    passport_country VARCHAR(50) NOT NULL,
                    destination_country VARCHAR(50) NOT NULL,
                    result TEXT NOT NULL,
                    checked_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (agent_id) REFERENCES users(id) ON DELETE CASCADE
                ) ENGINE=InnoDB;
            """,
            "agent_rewards": """
                CREATE TABLE agent_rewards (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    agent_id INT NOT NULL,
                    reward_points INT NOT NULL,
                    description VARCHAR(255),
                    awarded_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (agent_id) REFERENCES users(id) ON DELETE CASCADE
                ) ENGINE=InnoDB;
            """,
            "popups": """
                CREATE TABLE popups (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    message_text TEXT NOT NULL,
                    is_active BOOLEAN DEFAULT TRUE,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                ) ENGINE=InnoDB;
            """
        }
        
        # Create all tables
        for name, sql in table_schemas.items():
            cursor.execute(sql)
            print(f"Created table: {name}")
            
        # Seed users
        # 3 Agents: one premium high credit, one normal, one zero-credit
        # 1 Admin
        cursor.execute("""
            INSERT INTO users (username, password, email, role, credit_balance, company_name, phone, onboarded_at)
            VALUES 
            ('premium_agent', 'agent123', 'premium@travel.com', 'agent', 45000.00, 'XYZ Travels', '+1234567890', '2026-01-10 10:00:00'),
            ('standard_agent', 'agent123', 'standard@travel.com', 'agent', 7850.50, 'Global Tourers', '+1987654321', '2026-02-15 11:30:00'),
            ('zero_agent', 'agent123', 'zero@travel.com', 'agent', 0.00, 'Budget Flight Shop', '+1122334455', '2026-05-01 09:15:00'),
            ('admin', 'admin123', 'admin@atl.com', 'admin', 0.00, 'ATL Operations', '+1000000000', '2025-12-01 08:00:00')
        """)
        print("Seeded users table.")
        
        # Seed flights
        # We need LCC, NDC, and GDS (Amadeus/Sabre) flights
        flights_data = [
            ('QR-832', 'Qatar Airways', 'DOH', 'LHR', 'GDS', 'GDS', 1, 450.00, 48),
            ('EK-348', 'Emirates', 'DXB', 'SIN', 'GDS', 'GDS', 1, 620.00, 35),
            ('UL-101', 'SriLankan Airlines', 'CMB', 'MLE', 'LCC', 'LCC', 1, 150.00, 18),
            ('SQ-421', 'Singapore Airlines', 'SIN', 'SYD', 'NDC', 'NDC', 2, 750.00, 22),
            ('6E-451', 'IndiGo', 'DEL', 'CMB', 'LCC', 'LCC', 1, 180.00, 60),
            ('BA-117', 'British Airways', 'LHR', 'JFK', 'GDS', 'GDS', 1, 550.00, 40),
            ('UL-308', 'SriLankan Airlines', 'CMB', 'SIN', 'GDS', 'GDS', 1, 310.00, 28),
            
            # Seed flights for CMB <-> MEL Colombo-Melbourne
            ('EY-264', 'Etihad Airways', 'CMB', 'MEL', 'GDS', 'GDS', 2, 504.10, 9),
            ('EY-265', 'Etihad Airways', 'MEL', 'CMB', 'GDS', 'GDS', 2, 504.10, 9),
            ('6E-804', 'IndiGo', 'CMB', 'MEL', 'LCC', 'LCC', 2, 594.60, 9),
            ('6E-805', 'IndiGo', 'MEL', 'CMB', 'LCC', 'LCC', 2, 594.60, 9),
            ('MH-178', 'Malaysia Airlines', 'CMB', 'MEL', 'GDS', 'GDS', 2, 676.21, 9),
            ('MH-179', 'Malaysia Airlines', 'MEL', 'CMB', 'GDS', 'GDS', 2, 676.21, 9),
            ('CX-610', 'Cathay Pacific', 'CMB', 'MEL', 'NDC', 'NDC', 2, 787.05, 9),
            ('CX-611', 'Cathay Pacific', 'MEL', 'CMB', 'NDC', 'NDC', 2, 787.05, 9)
        ]

        
        now = datetime.datetime.now()
        for i, f in enumerate(flights_data):
            dep = now + datetime.timedelta(days=random.randint(2, 10), hours=random.randint(1, 23))
            arr = dep + datetime.timedelta(hours=f[6]) # Segment/Hours estimate
            cursor.execute("""
                INSERT INTO flights (flight_number, airline, origin, destination, flight_type, gds_source, departure_time, arrival_time, price, seats_available, segment_count)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, (f[0], f[1], f[2], f[3], f[4], f[5], dep, arr, f[7], f[8], f[6]))
            
        print("Seeded flights table.")
        
        # Seed hotels
        hotels_data = [
            ("Grand Plaza Hotel", "London, UK", 4, "A premium luxury boutique hotel right in the heart of London, offering elegant rooms and 5-star service.", "hotel_london.jpg"),
            ("Burj Al Arab Jumeirah", "Dubai, UAE", 5, "The global icon of Arabian luxury, towering over the Persian Gulf. Experience unparalleled world-class hospitality.", "hotel_dubai.jpg"),
            ("Paradise Island Resort", "Maldives", 5, "An luxury beach and overwater villa sanctuary in Maldives, surrounded by turquoise waters and white sandy beaches.", "hotel_maldives.jpg"),
            ("Changi Village Inn", "Singapore", 3, "A clean, modern, and affordable business hotel conveniently located near Changi Airport.", "hotel_singapore.jpg")
        ]
        for name, loc, stars, desc, img in hotels_data:
            cursor.execute("""
                INSERT INTO hotels (name, location, rating, description, image_url)
                VALUES (%s, %s, %s, %s, %s)
            """, (name, loc, stars, desc, img))
            
        print("Seeded hotels table.")
        
        # Seed rooms for hotels
        cursor.execute("SELECT id, name FROM hotels")
        hotels_list = cursor.fetchall()
        for hotel_id, name in hotels_list:
            if "London" in name or "Dubai" in name:
                cursor.execute("""
                    INSERT INTO rooms (hotel_id, room_type, price_per_night, availability)
                    VALUES 
                    (%s, 'Deluxe Double Room', 220.00, 1),
                    (%s, 'Executive Ocean Suite', 580.00, 1),
                    (%s, 'Presidential Penthouse', 1200.00, 1)
                """, (hotel_id, hotel_id, hotel_id))
            else:
                cursor.execute("""
                    INSERT INTO rooms (hotel_id, room_type, price_per_night, availability)
                    VALUES 
                    (%s, 'Standard Single Room', 95.00, 1),
                    (%s, 'Deluxe Lagoon Villa', 320.00, 1),
                    (%s, 'Overwater Bungalow', 650.00, 1)
                """, (hotel_id, hotel_id, hotel_id))
        print("Seeded rooms table.")
        
        # Seed default service fees (Markup / Markdown configs)
        # Type: issuance ($15 markup), re-issue ($25 markup), refund ($10 markup)
        cursor.execute("""
            INSERT INTO service_fees (transaction_type, fee_type, amount)
            VALUES 
            ('issuance', 'markup', 15.00),
            ('re-issue', 'markup', 25.00),
            ('refund', 'markup', 10.00)
        """)
        print("Seeded default service fees.")
        
        # Seed historical bookings to generate meaningful dashboard TO/GP charts
        # We need historical bookings for both premium_agent and standard_agent
        cursor.execute("SELECT id FROM users WHERE username = 'premium_agent'")
        prem_agent_id = cursor.fetchone()[0]
        cursor.execute("SELECT id FROM users WHERE username = 'standard_agent'")
        std_agent_id = cursor.fetchone()[0]
        
        cursor.execute("SELECT id, price, flight_number, flight_type, gds_source FROM flights")
        flights_pool = cursor.fetchall()
        cursor.execute("SELECT rooms.id, rooms.price_per_night, hotels.name FROM rooms JOIN hotels ON rooms.hotel_id = hotels.id")
        rooms_pool = cursor.fetchall()
        
        # Create a series of bookings over the last 6 months to make a stunning chart
        booking_types = ['flight', 'hotel']
        statuses = ['ticketed', 'ticketed', 'ticketed', 'refunded', 'voided']
        passenger_names = ["Sanka Lasitha", "Jane Doe", "John Smith", "David Villa", "Amara Silva", "Nisha Patel"]
        
        invoice_counter = 1000
        
        for months_ago in range(5, -1, -1):
            # Generate 3 bookings per month
            for _ in range(3):
                agent_id = random.choice([prem_agent_id, std_agent_id])
                b_type = random.choice(booking_types)
                status = random.choice(statuses)
                
                # Dynamic past date
                created_date = now - datetime.timedelta(days=months_ago*30 + random.randint(1, 28), hours=random.randint(1, 12))
                invoice_number = f"INV-{invoice_counter}"
                invoice_counter += 1
                
                if b_type == 'flight':
                    flight = random.choice(flights_pool)
                    fl_id, fl_price, fl_num, fl_type, gds_src = flight
                    orig_price = fl_price
                    markup = Decimal("15.00")
                    total = orig_price + markup
                    
                    cursor.execute("""
                        INSERT INTO bookings (agent_id, booking_type, status, total_price, invoice_number, created_at)
                        VALUES (%s, 'flight', %s, %s, %s, %s)
                    """, (agent_id, status, total, invoice_number, created_date))
                    booking_id = cursor.lastrowid
                    
                    pnr = f"PNR{random.randint(100000, 999999)}"
                    tkt = f"TKT-{random.randint(1000000000, 9999999999)}" if status == "ticketed" else None
                    cursor.execute("""
                        INSERT INTO flight_bookings (booking_id, flight_id, passenger_name, seat_number, gds_type, ticket_status, original_price, service_fee, pnr_reference, ticket_number)
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    """, (booking_id, fl_id, random.choice(passenger_names), f"{random.randint(12, 28)}{random.choice(['A','C','F'])}", fl_type, status, orig_price, markup, pnr, tkt))
                
                else: # hotel booking
                    room = random.choice(rooms_pool)
                    rm_id, rm_price, hotel_name = room
                    nights = random.randint(2, 5)
                    orig_price = rm_price * nights
                    markup = Decimal("25.00")
                    total = orig_price + markup
                    
                    cursor.execute("""
                        INSERT INTO bookings (agent_id, booking_type, status, total_price, invoice_number, created_at)
                        VALUES (%s, 'hotel', %s, %s, %s, %s)
                    """, (agent_id, status, total, invoice_number, created_date))
                    booking_id = cursor.lastrowid
                    
                    check_in = (created_date + datetime.timedelta(days=10)).date()
                    check_out = (check_in + datetime.timedelta(days=nights))
                    
                    cursor.execute("""
                        INSERT INTO hotel_bookings (booking_id, room_id, check_in, check_out, guest_name, original_price, service_fee)
                        VALUES (%s, %s, %s, %s, %s, %s, %s)
                    """, (booking_id, rm_id, check_in, check_out, random.choice(passenger_names), orig_price, markup))
                    
        print("Seeded historical bookings for Turnover & Gross Profit reports.")
        
        # Seed support tickets
        cursor.execute("""
            INSERT INTO support_tickets (agent_id, subject, message, status, created_at)
            VALUES 
            (%s, 'Amadeus API Timeout Issue', 'Hello ATL support, we noticed periodic timeouts when searching for GDS flights to LHR this morning around 9:00 AM. Please advise.', 'open', %s),
            (%s, 'Credit Top-Up Pending', 'We submitted a bank transfer for a $5,000 credit top-up, but it has not been activated yet. Reference code TXN-88741.', 'resolved', %s)
        """, (std_agent_id, now - datetime.timedelta(hours=4), prem_agent_id, now - datetime.timedelta(days=1)))
        print("Seeded agent support tickets.")
        
        # Seed Timatic visa logs
        cursor.execute("""
            INSERT INTO timatic_checks (agent_id, passport_country, destination_country, result, checked_at)
            VALUES 
            (%s, 'Sri Lanka', 'Maldives', 'Visa not required for tourist stays up to 30 days. Passport must be valid for at least 1 month. Confirm return ticket.', %s),
            (%s, 'India', 'United Kingdom', 'Standard Visitor Visa required. Applications must be completed online in advance. Biometrics collection required.', %s)
        """, (prem_agent_id, now - datetime.timedelta(days=2), std_agent_id, now - datetime.timedelta(days=3)))
        print("Seeded Timatic Visa checks logs.")
        
        # Seed agent rewards (loyalty points)
        cursor.execute("""
            INSERT INTO agent_rewards (agent_id, reward_points, description, awarded_at)
            VALUES 
            (%s, 500, 'Q1 High Performance Agent Bonus', %s),
            (%s, 150, 'Monthly Active Agent Reward', %s)
        """, (prem_agent_id, now - datetime.timedelta(days=15), std_agent_id, now - datetime.timedelta(days=5)))
        print("Seeded agent rewards & recognition data.")
        
        # Seed System popups
        cursor.execute("""
            INSERT INTO popups (message_text, is_active)
            VALUES 
            ('System Alert: Maintenance scheduled on Sunday from 02:00 AM to 04:00 AM GMT.', 1),
            ('Agent Advisory: Special NDC fares on Singapore Airlines now active with a discounted service markup of only $5!', 1)
        """)
        print("Seeded system pop-ups.")
        
        # Commit transaction
        conn.commit()
        cursor.close()
        conn.close()
        print("Database initialization and seeding completed successfully!")
        return True
        
    except mysql.connector.Error as err:
        print("Database error occurred:")
        print(err)
        return False

if __name__ == "__main__":
    initialize_database()
