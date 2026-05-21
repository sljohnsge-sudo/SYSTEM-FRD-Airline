from flask import Flask, render_template, request, redirect, url_for, session, jsonify
import mysql.connector
from decimal import Decimal
import datetime
import random
from amadeus import Client, ResponseError

app = Flask(__name__)
app.secret_key = "travel_portal_secret_key_amadeus_b2b"

# Helper for decimal JSON serialization
class DecimalEncoder:
    @staticmethod
    def encode(obj):
        if isinstance(obj, Decimal):
            return float(obj)
        if isinstance(obj, (datetime.datetime, datetime.date)):
            return obj.isoformat()
        raise TypeError("Type not serializable")

def get_db_connection():
    return mysql.connector.connect(
        host="127.0.0.1",
        user="root",
        password="",
        database="travel_booking_system"
    )

def query_db(query, args=(), one=False):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute(query, args)
    rv = cursor.fetchall()
    conn.commit()
    cursor.close()
    conn.close()
    return (rv[0] if rv else None) if one else rv

# Route: Home/Redirect
@app.route("/")
def index():
    if "user_id" in session:
        if session["role"] == "admin":
            return redirect(url_for("admin_dashboard"))
        return redirect(url_for("agent_dashboard"))
    return render_template("welcome.html")

# Route: Login
@app.route("/login", methods=["GET", "POST"])
def login():
    error = None
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")
        
        user = query_db("SELECT * FROM users WHERE username = %s AND password = %s", (username, password), one=True)
        if user:
            session["user_id"] = user["id"]
            session["username"] = user["username"]
            session["role"] = user["role"]
            session["company_name"] = user["company_name"]
            
            if user["role"] == "admin":
                return redirect(url_for("admin_dashboard"))
            return redirect(url_for("agent_dashboard"))
        else:
            error = "Invalid username or password."
            
    return render_template("login.html", error=error)

# Route: Logout
@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))

# Route: Agent Dashboard
@app.route("/agent")
def agent_dashboard():
    if "user_id" not in session or session["role"] != "agent":
        return redirect(url_for("login"))
    
    agent_id = session["user_id"]
    agent_info = query_db("SELECT * FROM users WHERE id = %s", (agent_id,), one=True)
    
    # Get active popups
    popups = query_db("SELECT * FROM popups WHERE is_active = 1 ORDER BY created_at DESC")
    
    # Get flight list for search default
    flights = query_db("SELECT * FROM flights ORDER BY price ASC")
    
    # Get hotels list for search default
    hotels = query_db("SELECT * FROM hotels ORDER BY rating DESC")
    
    return render_template("agent_dashboard.html", agent=agent_info, popups=popups, flights=flights, hotels=hotels)

# Route: Admin Dashboard
@app.route("/admin")
def admin_dashboard():
    if "user_id" not in session or session["role"] != "admin":
        return redirect(url_for("login"))
    
    admin_info = query_db("SELECT * FROM users WHERE id = %s", (session["user_id"],), one=True)
    return render_template("admin_dashboard.html", admin=admin_info)

# =========================================================================
# B2B AGENT API ENDPOINTS
# =========================================================================

# API: Get Agent Info
@app.route("/api/agent/info")
def api_agent_info():
    if "user_id" not in session or session["role"] != "agent":
        return jsonify({"success": False, "error": "Unauthorized"}), 401
    
    agent = query_db("SELECT id, username, email, credit_balance, company_name, phone FROM users WHERE id = %s", (session["user_id"],), one=True)
    agent["credit_balance"] = float(agent["credit_balance"])
    
    # Get reward points
    rewards = query_db("SELECT SUM(reward_points) as total FROM agent_rewards WHERE agent_id = %s", (session["user_id"],), one=True)
    agent["reward_points"] = rewards["total"] if rewards["total"] else 0
    
    return jsonify({"success": True, "agent": agent})

# API: Top-Up Credit (Instant Payment Update)
@app.route("/api/agent/topup", methods=["POST"])
def api_agent_topup():
    if "user_id" not in session or session["role"] != "agent":
        return jsonify({"success": False, "error": "Unauthorized"}), 401
    
    amount = request.json.get("amount")
    if not amount or float(amount) <= 0:
        return jsonify({"success": False, "error": "Invalid top-up amount"}), 400
        
    amount_dec = Decimal(str(amount))
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute("UPDATE users SET credit_balance = credit_balance + %s WHERE id = %s", (amount_dec, session["user_id"]))
        conn.commit()
        
        # Get updated balance
        cursor.execute("SELECT credit_balance FROM users WHERE id = %s", (session["user_id"],))
        new_balance = float(cursor.fetchone()[0])
        
        cursor.close()
        conn.close()
        return jsonify({"success": True, "new_balance": new_balance, "message": "Payment processed instantly! Credit balance updated."})
    except Exception as e:
        conn.rollback()
        cursor.close()
        conn.close()
        return jsonify({"success": False, "error": str(e)}), 500

# API: Search Flights (GDS, LCC, NDC consolidated)
@app.route("/api/flights/search", methods=["GET"])
def api_flights_search():
    origin = request.args.get("origin", "").strip().upper()
    destination = request.args.get("destination", "").strip().upper()
    flight_type = request.args.get("flight_type", "ALL") # ALL, GDS, LCC, NDC
    date_str = request.args.get("date", (datetime.datetime.now() + datetime.timedelta(days=7)).strftime("%Y-%m-%d")).strip()
    
    # Pre-fetch live GDS flights from Amadeus API and cache them in local database
    if flight_type in ["ALL", "GDS"] and origin and destination:
        try:
            amadeus = Client(
                client_id='3ZBEyT1bTUzMUPkcEPBUOEKIAkEjgu5o',
                client_secret='2K9Xh5GC2UF9rVo3',
                hostname='test'
            )
            response = amadeus.shopping.flight_offers_search.get(
                originLocationCode=origin,
                destinationLocationCode=destination,
                departureDate=date_str,
                adults=1,
                max=10
            )
            
            conn = get_db_connection()
            cursor = conn.cursor()
            for f in response.data:
                segments = f['itineraries'][0]['segments']
                flight_no = f"{segments[0]['carrierCode']}-{segments[0]['number']}"
                airline = segments[0]['carrierCode']
                price_val = Decimal(str(f['price']['total']))
                # Keep first 19 chars for mysql datetime format (YYYY-MM-DD HH:MM:SS)
                dept = segments[0]['departure']['at'].replace('T', ' ')[:19]
                arr = segments[-1]['arrival']['at'].replace('T', ' ')[:19]
                
                # Avoid duplicates
                cursor.execute("SELECT id FROM flights WHERE flight_number = %s AND departure_time = %s", (flight_no, dept))
                if not cursor.fetchone():
                    cursor.execute("""
                        INSERT INTO flights (flight_number, airline, origin, destination, departure_time, arrival_time, price, seats_available, flight_type)
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, 'GDS')
                    """, (flight_no, airline, origin, destination, dept, arr, price_val, f.get('numberOfBookableSeats', 9)))
            conn.commit()
            cursor.close()
            conn.close()
        except Exception as e:
            print("Amadeus API error:", e)

    query = "SELECT * FROM flights WHERE 1=1"
    params = []
    
    if origin:
        query += " AND origin = %s"
        params.append(origin)
    if destination:
        query += " AND destination = %s"
        params.append(destination)
    if flight_type != "ALL":
        query += " AND flight_type = %s"
        params.append(flight_type)
        
    query += " ORDER BY price ASC"
    
    flights = query_db(query, tuple(params))
    
    # Format decimals for JSON
    for f in flights:
        f["price"] = float(f["price"])
        f["departure_time"] = f["departure_time"].isoformat()
        f["arrival_time"] = f["arrival_time"].isoformat()
        f["segment_count"] = 1
        
    return jsonify({"success": True, "flights": flights})

# API: Flight Booking (with automatic markup application and credit limit validation)
@app.route("/api/flights/book", methods=["POST"])
def api_flights_book():
    if "user_id" not in session or session["role"] != "agent":
        return jsonify({"success": False, "error": "Unauthorized"}), 401
        
    data = request.json
    flight_id = data.get("flight_id")
    passenger_name = data.get("passenger_name")
    seat_number = data.get("seat_number", "14A")
    ticket_now = data.get("ticket_now", False) # True = Ticketed, False = Non-Ticketed reservation
    
    if not flight_id or not passenger_name:
        return jsonify({"success": False, "error": "Flight and passenger name are required"}), 400
        
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    
    try:
        # Get flight details
        cursor.execute("SELECT * FROM flights WHERE id = %s", (flight_id,))
        flight = cursor.fetchone()
        if not flight:
            return jsonify({"success": False, "error": "Flight not found"}), 404
            
        if flight["seats_available"] <= 0:
            return jsonify({"success": False, "error": "No seats available on this flight"}), 400
            
        # Get issuance markup
        cursor.execute("SELECT amount FROM service_fees WHERE transaction_type = 'issuance'")
        fee = cursor.fetchone()
        markup = Decimal(str(fee["amount"])) if fee else Decimal("15.00")
        
        orig_price = flight["price"]
        total_price = orig_price + markup
        
        # Check credit balance
        cursor.execute("SELECT credit_balance FROM users WHERE id = %s", (session["user_id"],))
        agent_credit = cursor.fetchone()["credit_balance"]
        
        # If user chooses to ticket immediately, credit must be checked
        booking_status = "ticketed" if ticket_now else "non-ticketed"
        
        if booking_status == "ticketed" and agent_credit < total_price:
            return jsonify({
                "success": False, 
                "error": "Insufficient credit balance to ticket this booking. Please top up your account.",
                "code": "INSUFFICIENT_CREDIT"
            }), 400
            
        # Generate Invoice and Booking
        invoice_number = f"INV-F{random.randint(100000, 999999)}"
        cursor.execute("""
            INSERT INTO bookings (agent_id, booking_type, status, total_price, invoice_number, created_at)
            VALUES (%s, 'flight', %s, %s, %s, NOW())
        """, (session["user_id"], booking_status, total_price, invoice_number))
        
        booking_id = cursor.lastrowid
        
        # Insert flight booking details
        cursor.execute("""
            INSERT INTO flight_bookings (booking_id, flight_id, passenger_name, seat_number, gds_type, ticket_status, original_price, service_fee)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        """, (booking_id, flight_id, passenger_name, seat_number, flight["flight_type"], booking_status, orig_price, markup))
        
        # Deduct credit if ticketed
        if booking_status == "ticketed":
            cursor.execute("UPDATE users SET credit_balance = credit_balance - %s WHERE id = %s", (total_price, session["user_id"]))
            # Deduct seat count
            cursor.execute("UPDATE flights SET seats_available = seats_available - 1 WHERE id = %s", (flight_id,))
            
            # Award loyalty rewards
            reward_points = int(total_price / 10)
            cursor.execute("""
                INSERT INTO agent_rewards (agent_id, reward_points, description)
                VALUES (%s, %s, %s)
            """, (session["user_id"], reward_points, f"Points earned for Flight Ticket {invoice_number}"))
            
        conn.commit()
        cursor.close()
        conn.close()
        
        status_message = "Ticketed successfully! Invoice generated." if booking_status == "ticketed" else "Reservation saved as Non-Ticketed (Credit not deducted)."
        return jsonify({
            "success": True, 
            "message": status_message, 
            "invoice_number": invoice_number,
            "total_price": float(total_price),
            "booking_id": booking_id
        })
        
    except Exception as e:
        conn.rollback()
        cursor.close()
        conn.close()
        return jsonify({"success": False, "error": str(e)}), 500

# API: Search Hotels
@app.route("/api/hotels/search", methods=["GET"])
def api_hotels_search():
    location = request.args.get("location", "").strip()
    
    query = "SELECT * FROM hotels WHERE 1=1"
    params = []
    
    if location:
        query += " AND location LIKE %s"
        params.append(f"%{location}%")
        
    hotels = query_db(query, tuple(params))
    
    # Fetch rooms for each hotel
    for h in hotels:
        rooms = query_db("SELECT * FROM rooms WHERE hotel_id = %s AND availability = 1", (h["id"],))
        for r in rooms:
            r["price_per_night"] = float(r["price_per_night"])
        h["rooms"] = rooms
        
    return jsonify({"success": True, "hotels": hotels})

# API: Book Hotel
@app.route("/api/hotels/book", methods=["POST"])
def api_hotels_book():
    if "user_id" not in session or session["role"] != "agent":
        return jsonify({"success": False, "error": "Unauthorized"}), 401
        
    data = request.json
    room_id = data.get("room_id")
    guest_name = data.get("guest_name")
    check_in_str = data.get("check_in")
    check_out_str = data.get("check_out")
    
    if not room_id or not guest_name or not check_in_str or not check_out_str:
        return jsonify({"success": False, "error": "All fields are required"}), 400
        
    try:
        check_in = datetime.datetime.strptime(check_in_str, "%Y-%m-%d").date()
        check_out = datetime.datetime.strptime(check_out_str, "%Y-%m-%d").date()
        nights = (check_out - check_in).days
        if nights <= 0:
            return jsonify({"success": False, "error": "Check-out date must be after Check-in"}), 400
    except ValueError:
        return jsonify({"success": False, "error": "Invalid date format. Use YYYY-MM-DD"}), 400
        
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    
    try:
        # Check room details
        cursor.execute("SELECT * FROM rooms WHERE id = %s AND availability = 1", (room_id,))
        room = cursor.fetchone()
        if not room:
            return jsonify({"success": False, "error": "Room not available or not found"}), 404
            
        # Get hotel name
        cursor.execute("SELECT name FROM hotels WHERE id = %s", (room["hotel_id"],))
        hotel_name = cursor.fetchone()["name"]
        
        # Calculate pricing
        orig_price = room["price_per_night"] * nights
        markup = Decimal("25.00") # Hotel booking fixed service fee
        total_price = orig_price + markup
        
        # Check credit balance
        cursor.execute("SELECT credit_balance FROM users WHERE id = %s", (session["user_id"],))
        agent_credit = cursor.fetchone()["credit_balance"]
        
        if agent_credit < total_price:
            return jsonify({
                "success": False, 
                "error": "Insufficient credit balance. Please top up your account.",
                "code": "INSUFFICIENT_CREDIT"
            }), 400
            
        # Book room: ticketed status
        invoice_number = f"INV-H{random.randint(100000, 999999)}"
        cursor.execute("""
            INSERT INTO bookings (agent_id, booking_type, status, total_price, invoice_number, created_at)
            VALUES (%s, 'hotel', 'ticketed', %s, %s, NOW())
        """, (session["user_id"], total_price, invoice_number))
        
        booking_id = cursor.lastrowid
        
        # Insert hotel details
        cursor.execute("""
            INSERT INTO hotel_bookings (booking_id, room_id, check_in, check_out, guest_name, original_price, service_fee)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
        """, (booking_id, room_id, check_in, check_out, guest_name, orig_price, markup))
        
        # Deduct agent credit
        cursor.execute("UPDATE users SET credit_balance = credit_balance - %s WHERE id = %s", (total_price, session["user_id"]))
        
        # Award loyalty points
        reward_points = int(total_price / 10)
        cursor.execute("""
            INSERT INTO agent_rewards (agent_id, reward_points, description)
            VALUES (%s, %s, %s)
        """, (session["user_id"], reward_points, f"Points earned for Hotel {hotel_name} invoice {invoice_number}"))
        
        conn.commit()
        cursor.close()
        conn.close()
        
        return jsonify({
            "success": True, 
            "message": "Hotel booked successfully! Invoice raised.",
            "invoice_number": invoice_number,
            "total_price": float(total_price)
        })
        
    except Exception as e:
        conn.rollback()
        cursor.close()
        conn.close()
        return jsonify({"success": False, "error": str(e)}), 500

# API: Get Bookings List
@app.route("/api/bookings/list")
def api_bookings_list():
    if "user_id" not in session:
        return jsonify({"success": False, "error": "Unauthorized"}), 401
        
    # Standard agent only sees their own; Admin sees all
    query_params = []
    if session["role"] == "agent":
        query = "SELECT * FROM bookings WHERE agent_id = %s ORDER BY created_at DESC"
        query_params.append(session["user_id"])
    else:
        query = "SELECT bookings.*, users.username, users.company_name FROM bookings JOIN users ON bookings.agent_id = users.id ORDER BY created_at DESC"
        
    bookings = query_db(query, tuple(query_params))
    
    # Fetch specifics for each booking
    for b in bookings:
        b["total_price"] = float(b["total_price"])
        b["created_at"] = b["created_at"].isoformat()
        
        if b["booking_type"] == "flight":
            details = query_db("""
                SELECT flight_bookings.*, flights.flight_number, flights.airline, flights.origin, flights.destination, flights.departure_time 
                FROM flight_bookings 
                JOIN flights ON flight_bookings.flight_id = flights.id 
                WHERE flight_bookings.booking_id = %s
            """, (b["id"],), one=True)
            if details:
                details["original_price"] = float(details["original_price"])
                details["service_fee"] = float(details["service_fee"])
                details["departure_time"] = details["departure_time"].isoformat()
                b["details"] = details
        else:
            details = query_db("""
                SELECT hotel_bookings.*, rooms.room_type, hotels.name as hotel_name, hotels.location 
                FROM hotel_bookings 
                JOIN rooms ON hotel_bookings.room_id = rooms.id 
                JOIN hotels ON rooms.hotel_id = hotels.id 
                WHERE hotel_bookings.booking_id = %s
            """, (b["id"],), one=True)
            if details:
                details["original_price"] = float(details["original_price"])
                details["service_fee"] = float(details["service_fee"])
                details["check_in"] = details["check_in"].isoformat()
                details["check_out"] = details["check_out"].isoformat()
                b["details"] = details
                
    return jsonify({"success": True, "bookings": bookings})

# API: Ticketing a Reservation (Non-Ticketed -> Ticketed)
@app.route("/api/bookings/ticket", methods=["POST"])
def api_bookings_ticket():
    if "user_id" not in session or session["role"] != "agent":
        return jsonify({"success": False, "error": "Unauthorized"}), 401
        
    booking_id = request.json.get("booking_id")
    
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    
    try:
        # Check booking details
        cursor.execute("SELECT * FROM bookings WHERE id = %s AND agent_id = %s AND status = 'non-ticketed'", (booking_id, session["user_id"]))
        booking = cursor.fetchone()
        if not booking:
            return jsonify({"success": False, "error": "Non-ticketed booking not found"}), 404
            
        total_price = booking["total_price"]
        
        # Check credit
        cursor.execute("SELECT credit_balance FROM users WHERE id = %s", (session["user_id"],))
        agent_credit = cursor.fetchone()["credit_balance"]
        
        if agent_credit < total_price:
            return jsonify({"success": False, "error": "Insufficient credit balance to ticket this reservation.", "code": "INSUFFICIENT_CREDIT"}), 400
            
        # Update status
        cursor.execute("UPDATE bookings SET status = 'ticketed' WHERE id = %s", (booking_id,))
        cursor.execute("UPDATE flight_bookings SET ticket_status = 'ticketed' WHERE booking_id = %s", (booking_id,))
        
        # Deduct credit
        cursor.execute("UPDATE users SET credit_balance = credit_balance - %s WHERE id = %s", (total_price, session["user_id"]))
        
        # Deduct seat on flight
        cursor.execute("SELECT flight_id FROM flight_bookings WHERE booking_id = %s", (booking_id,))
        flight_id = cursor.fetchone()["flight_id"]
        cursor.execute("UPDATE flights SET seats_available = seats_available - 1 WHERE id = %s", (flight_id,))
        
        # Award loyalty points
        reward_points = int(total_price / 10)
        cursor.execute("""
            INSERT INTO agent_rewards (agent_id, reward_points, description)
            VALUES (%s, %s, %s)
        """, (session["user_id"], reward_points, f"Points earned for ticket issuance {booking['invoice_number']}"))
        
        conn.commit()
        cursor.close()
        conn.close()
        return jsonify({"success": True, "message": "Reservation ticketed successfully! Balance updated."})
        
    except Exception as e:
        conn.rollback()
        cursor.close()
        conn.close()
        return jsonify({"success": False, "error": str(e)}), 500

# API: Auto Re-Issue Simulator (Automated Ticket Changes - ATC)
@app.route("/api/bookings/reissue", methods=["POST"])
def api_bookings_reissue():
    if "user_id" not in session or session["role"] != "agent":
        return jsonify({"success": False, "error": "Unauthorized"}), 401
        
    booking_id = request.json.get("booking_id")
    new_flight_id = request.json.get("new_flight_id")
    
    if not booking_id or not new_flight_id:
        return jsonify({"success": False, "error": "Booking and target Flight are required"}), 400
        
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    
    try:
        # Check current booking
        cursor.execute("""
            SELECT bookings.*, flight_bookings.original_price, flight_bookings.flight_id 
            FROM bookings 
            JOIN flight_bookings ON bookings.id = flight_bookings.booking_id
            WHERE bookings.id = %s AND bookings.agent_id = %s AND bookings.status = 'ticketed'
        """, (booking_id, session["user_id"]))
        curr_booking = cursor.fetchone()
        
        if not curr_booking:
            return jsonify({"success": False, "error": "Ticketed flight booking not found"}), 404
            
        # Get target flight details
        cursor.execute("SELECT * FROM flights WHERE id = %s", (new_flight_id,))
        new_flight = cursor.fetchone()
        if not new_flight:
            return jsonify({"success": False, "error": "New flight not found"}), 404
            
        # Get Configured Re-Issue Fee Markup
        cursor.execute("SELECT amount FROM service_fees WHERE transaction_type = 're-issue'")
        fee = cursor.fetchone()
        reissue_markup = Decimal(str(fee["amount"])) if fee else Decimal("25.00")
        
        # Amadeus Penalty Notifier Logic
        # Let's say penalty is 10% of old flight cost or flat $50
        amadeus_penalty = Decimal("50.00")
        
        old_price = curr_booking["original_price"]
        new_price = new_flight["price"]
        fare_difference = max(Decimal("0.00"), new_price - old_price)
        
        total_reissue_cost = amadeus_penalty + fare_difference + reissue_markup
        
        # Verify credit balance
        cursor.execute("SELECT credit_balance FROM users WHERE id = %s", (session["user_id"],))
        agent_credit = cursor.fetchone()["credit_balance"]
        
        if agent_credit < total_reissue_cost:
            return jsonify({
                "success": False, 
                "error": f"Insufficient credit to process auto re-issue. Required: ${total_reissue_cost:.2f}. Balance: ${agent_credit:.2f}",
                "code": "INSUFFICIENT_CREDIT"
            }), 400
            
        # Deduct credit
        cursor.execute("UPDATE users SET credit_balance = credit_balance - %s WHERE id = %s", (total_reissue_cost, session["user_id"]))
        
        # Update flight booking details to the new flight
        cursor.execute("UPDATE flight_bookings SET flight_id = %s, original_price = %s, service_fee = service_fee + %s WHERE booking_id = %s", 
                       (new_flight_id, new_price, reissue_markup, booking_id))
        
        # Update main booking total price
        cursor.execute("UPDATE bookings SET total_price = total_price + %s WHERE id = %s", (total_reissue_cost, booking_id))
        
        # Restore seat on old flight, deduct seat on new flight
        cursor.execute("UPDATE flights SET seats_available = seats_available + 1 WHERE id = %s", (curr_booking["flight_id"],))
        cursor.execute("UPDATE flights SET seats_available = seats_available - 1 WHERE id = %s", (new_flight_id,))
        
        conn.commit()
        cursor.close()
        conn.close()
        
        return jsonify({
            "success": True,
            "message": "Auto Re-Issue (ATC) processed instantly via Flight Hub!",
            "details": {
                "amadeus_penalty": float(amadeus_penalty),
                "fare_difference": float(fare_difference),
                "service_markup": float(reissue_markup),
                "total_charged": float(total_reissue_cost)
            }
        })
        
    except Exception as e:
        conn.rollback()
        cursor.close()
        conn.close()
        return jsonify({"success": False, "error": str(e)}), 500

# API: Auto Refund Simulator (Ticket Refund Functionality - TRF)
@app.route("/api/bookings/refund", methods=["POST"])
def api_bookings_refund():
    if "user_id" not in session or session["role"] != "agent":
        return jsonify({"success": False, "error": "Unauthorized"}), 401
        
    booking_id = request.json.get("booking_id")
    
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    
    try:
        # Check current booking
        cursor.execute("""
            SELECT * FROM bookings WHERE id = %s AND agent_id = %s AND status = 'ticketed'
        """, (booking_id, session["user_id"]))
        booking = cursor.fetchone()
        
        if not booking:
            return jsonify({"success": False, "error": "Ticketed booking not found"}), 404
            
        # Get Configured Refund Fee Markup
        cursor.execute("SELECT amount FROM service_fees WHERE transaction_type = 'refund'")
        fee = cursor.fetchone()
        refund_markup = Decimal(str(fee["amount"])) if fee else Decimal("10.00")
        
        # Amadeus penalty (typically flat $75 for refunds)
        amadeus_penalty = Decimal("75.00")
        
        original_price = booking["total_price"]
        
        # Calculated refund value: original paid price minus Amadeus penalty and minus our refund processing fee
        refund_amount = original_price - amadeus_penalty - refund_markup
        
        if refund_amount < 0:
            refund_amount = Decimal("0.00")
            
        # Update booking status to refunded
        cursor.execute("UPDATE bookings SET status = 'refunded' WHERE id = %s", (booking_id,))
        
        if booking["booking_type"] == "flight":
            cursor.execute("UPDATE flight_bookings SET ticket_status = 'refunded' WHERE booking_id = %s", (booking_id,))
            # Restore flight seat
            cursor.execute("SELECT flight_id FROM flight_bookings WHERE booking_id = %s", (booking_id,))
            flight_id = cursor.fetchone()["flight_id"]
            cursor.execute("UPDATE flights SET seats_available = seats_available + 1 WHERE id = %s", (flight_id,))
        else:
            # Hotel Booking refund does not restore rooms dynamically in this simple schema but marks status
            cursor.execute("SELECT room_id FROM hotel_bookings WHERE booking_id = %s", (booking_id,))
            
        # Credit refund back to agent instantly
        cursor.execute("UPDATE users SET credit_balance = credit_balance + %s WHERE id = %s", (refund_amount, session["user_id"]))
        
        conn.commit()
        cursor.close()
        conn.close()
        
        return jsonify({
            "success": True,
            "message": "Ticket Refund Functionality (TRF) processed instantly! Account credited.",
            "details": {
                "original_ticket_price": float(original_price),
                "amadeus_cancellation_penalty": float(amadeus_penalty),
                "refund_service_markup": float(refund_markup),
                "net_refund_credited": float(refund_amount)
            }
        })
        
    except Exception as e:
        conn.rollback()
        cursor.close()
        conn.close()
        return jsonify({"success": False, "error": str(e)}), 500

# API: Void Reservation
@app.route("/api/bookings/void", methods=["POST"])
def api_bookings_void():
    if "user_id" not in session or session["role"] != "agent":
        return jsonify({"success": False, "error": "Unauthorized"}), 401
        
    booking_id = request.json.get("booking_id")
    
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    
    try:
        # Void is allowed only for non-ticketed bookings (free release of seat) or within 24h (we allow all non-ticketed)
        cursor.execute("SELECT * FROM bookings WHERE id = %s AND agent_id = %s AND status = 'non-ticketed'", (booking_id, session["user_id"]))
        booking = cursor.fetchone()
        if not booking:
            return jsonify({"success": False, "error": "Only non-ticketed reservations can be voided without penalty."}), 400
            
        cursor.execute("UPDATE bookings SET status = 'voided' WHERE id = %s", (booking_id,))
        if booking["booking_type"] == "flight":
            cursor.execute("UPDATE flight_bookings SET ticket_status = 'voided' WHERE booking_id = %s", (booking_id,))
            
        conn.commit()
        cursor.close()
        conn.close()
        return jsonify({"success": True, "message": "Reservation voided and cancelled successfully."})
        
    except Exception as e:
        conn.rollback()
        cursor.close()
        conn.close()
        return jsonify({"success": False, "error": str(e)}), 500

# API: Timatic Visa Tool Simulation
@app.route("/api/timatic/check", methods=["POST"])
def api_timatic_check():
    if "user_id" not in session or session["role"] != "agent":
        return jsonify({"success": False, "error": "Unauthorized"}), 401
        
    data = request.json
    passport = data.get("passport", "").strip()
    destination = data.get("destination", "").strip()
    
    if not passport or not destination:
        return jsonify({"success": False, "error": "Passport and Destination countries are required."}), 400
        
    # Standard Simulated Timatic Database Responses
    visa_rules = {
        "Maldives": "Visa not required for stays up to 30 days. Visitors must possess a passport valid for at least 1 month, a return flight ticket, and proof of funds ($100/day).",
        "United Kingdom": "Visa REQUIRED. Citizens passport requires a standard visitor visa. Must apply online at least 3 weeks prior. biometric identification mandatory.",
        "Singapore": "Visa not required for tourist stays up to 90 days. Passport must be valid for at least 6 months. SG Arrival Card (SGAC) must be submitted online 3 days before entry.",
        "United States": "Visa REQUIRED or ESTA authorization required. Passport must be valid for at least 6 months. Machine-readable requirements apply.",
        "Sri Lanka": "Electronic Travel Authorization (ETA) required prior to departure. Visa valid for 30 days initially. Return ticket required."
    }
    
    # Default fallback
    result = visa_rules.get(destination, f"Visa rules for travel from {passport} to {destination}: ETA/Visa is generally required for tourism stays. Passport must have 6 months validity. Please consult embassy.")
    
    # Log the timatic query in the database
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("""
            INSERT INTO timatic_checks (agent_id, passport_country, destination_country, result, checked_at)
            VALUES (%s, %s, %s, %s, NOW())
        """, (session["user_id"], passport, destination, result))
        conn.commit()
        cursor.close()
        conn.close()
    except Exception as e:
        cursor.close()
        conn.close()
        print("Failed to log Timatic check:", str(e))
        
    return jsonify({"success": True, "passport": passport, "destination": destination, "result": result})

# API: Get Timatic Logs
@app.route("/api/timatic/logs")
def api_timatic_logs():
    if "user_id" not in session or session["role"] != "agent":
        return jsonify({"success": False, "error": "Unauthorized"}), 401
        
    logs = query_db("SELECT * FROM timatic_checks WHERE agent_id = %s ORDER BY checked_at DESC LIMIT 5", (session["user_id"],))
    for l in logs:
        l["checked_at"] = l["checked_at"].isoformat()
    return jsonify({"success": True, "logs": logs})

# API: Support Tickets - Submit Feedback
@app.route("/api/support/create", methods=["POST"])
def api_support_create():
    if "user_id" not in session or session["role"] != "agent":
        return jsonify({"success": False, "error": "Unauthorized"}), 401
        
    data = request.json
    subject = data.get("subject", "").strip()
    message = data.get("message", "").strip()
    
    if not subject or not message:
        return jsonify({"success": False, "error": "Subject and message are required"}), 400
        
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("""
            INSERT INTO support_tickets (agent_id, subject, message, status, created_at)
            VALUES (%s, %s, %s, 'open', NOW())
        """, (session["user_id"], subject, message))
        conn.commit()
        cursor.close()
        conn.close()
        return jsonify({"success": True, "message": "Support request submitted successfully! Helpdesk ticket created."})
    except Exception as e:
        conn.rollback()
        cursor.close()
        conn.close()
        return jsonify({"success": False, "error": str(e)}), 500

# API: Get Support Tickets
@app.route("/api/support/list")
def api_support_list():
    if "user_id" not in session:
        return jsonify({"success": False, "error": "Unauthorized"}), 401
        
    if session["role"] == "agent":
        tickets = query_db("SELECT * FROM support_tickets WHERE agent_id = %s ORDER BY created_at DESC", (session["user_id"],))
    else:
        tickets = query_db("SELECT support_tickets.*, users.username, users.company_name FROM support_tickets JOIN users ON support_tickets.agent_id = users.id ORDER BY created_at DESC")
        
    for t in tickets:
        t["created_at"] = t["created_at"].isoformat()
    return jsonify({"success": True, "tickets": tickets})

# API: Daily Lowest Fares Display (Consolidated LCC/NDC/GDS)
@app.route("/api/flights/lowest-fares")
def api_flights_lowest_fares():
    # Show lowest fare available per destination and airline
    fares = query_db("""
        SELECT origin, destination, airline, MIN(price) as lowest_fare, flight_type
        FROM flights
        GROUP BY origin, destination, airline, flight_type
        ORDER BY lowest_fare ASC
    """)
    for f in fares:
        f["lowest_fare"] = float(f["lowest_fare"])
    return jsonify({"success": True, "fares": fares})


# API: TO/GP Reports (Agent & Admin)
@app.route("/api/reports/togp")
def api_reports_togp():
    if "user_id" not in session:
        return jsonify({"success": False, "error": "Unauthorized"}), 401
        
    agent_id = request.args.get("agent_id")
    
    # Filter by agent if it's agent portal
    where_clause = ""
    params = []
    if session["role"] == "agent":
        where_clause = " WHERE b.agent_id = %s"
        params.append(session["user_id"])
    elif agent_id and agent_id != "all":
        where_clause = " WHERE b.agent_id = %s"
        params.append(agent_id)
        
    # Generate Daily, Monthly, and Yearly Turnover and Gross Profit details
    # GP is calculated as the sum of all service_fees (which represents the markup)
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    
    # 1. Monthly summary for Chart (last 6 months)
    monthly_query = f"""
        SELECT 
            DATE_FORMAT(b.created_at, '%Y-%m') as month_label,
            SUM(b.total_price) as turnover,
            SUM(
                CASE 
                    WHEN b.booking_type = 'flight' THEN fb.service_fee
                    ELSE hb.service_fee
                END
            ) as gp
        FROM bookings b
        LEFT JOIN flight_bookings fb ON b.id = fb.booking_id
        LEFT JOIN hotel_bookings hb ON b.id = hb.booking_id
        {where_clause}
        GROUP BY month_label
        ORDER BY month_label ASC
        LIMIT 6
    """
    cursor.execute(monthly_query, tuple(params))
    monthly_data = cursor.fetchall()
    
    # Convert decimals to float
    for m in monthly_data:
        m["turnover"] = float(m["turnover"]) if m["turnover"] else 0.0
        m["gp"] = float(m["gp"]) if m["gp"] else 0.0
        m["cost"] = m["turnover"] - m["gp"]
        
    # 2. Daily Summary for reports
    daily_query = f"""
        SELECT 
            DATE(b.created_at) as day_label,
            SUM(b.total_price) as turnover,
            SUM(
                CASE 
                    WHEN b.booking_type = 'flight' THEN fb.service_fee
                    ELSE hb.service_fee
                END
            ) as gp
        FROM bookings b
        LEFT JOIN flight_bookings fb ON b.id = fb.booking_id
        LEFT JOIN hotel_bookings hb ON b.id = hb.booking_id
        {where_clause}
        GROUP BY day_label
        ORDER BY day_label DESC
        LIMIT 15
    """
    cursor.execute(daily_query, tuple(params))
    daily_data = cursor.fetchall()
    for d in daily_data:
        d["day_label"] = d["day_label"].isoformat()
        d["turnover"] = float(d["turnover"]) if d["turnover"] else 0.0
        d["gp"] = float(d["gp"]) if d["gp"] else 0.0
        
    # 3. Categorized Split Reports: by Airline
    airline_query = f"""
        SELECT 
            f.airline,
            COUNT(fb.id) as tickets_issued,
            SUM(b.total_price) as turnover,
            SUM(fb.service_fee) as gp
        FROM bookings b
        JOIN flight_bookings fb ON b.id = fb.booking_id
        JOIN flights f ON fb.flight_id = f.id
        {where_clause.replace('b.agent_id', 'b.agent_id')}
        GROUP BY f.airline
        ORDER BY turnover DESC
    """
    cursor.execute(airline_query, tuple(params))
    airline_data = cursor.fetchall()
    for a in airline_data:
        a["turnover"] = float(a["turnover"]) if a["turnover"] else 0.0
        a["gp"] = float(a["gp"]) if a["gp"] else 0.0
        
    # 4. Categorized Split Reports: by Destination
    dest_query = f"""
        SELECT 
            CASE 
                WHEN b.booking_type = 'flight' THEN f.destination
                ELSE h.location
            END as destination,
            COUNT(b.id) as booking_count,
            SUM(b.total_price) as turnover,
            SUM(
                CASE 
                    WHEN b.booking_type = 'flight' THEN fb.service_fee
                    ELSE hb.service_fee
                END
            ) as gp
        FROM bookings b
        LEFT JOIN flight_bookings fb ON b.id = fb.booking_id
        LEFT JOIN flights f ON fb.flight_id = f.id
        LEFT JOIN hotel_bookings hb ON b.id = hb.booking_id
        LEFT JOIN rooms r ON hb.room_id = r.id
        LEFT JOIN hotels h ON r.hotel_id = h.id
        {where_clause}
        GROUP BY destination
        ORDER BY turnover DESC
    """
    cursor.execute(dest_query, tuple(params))
    dest_data = cursor.fetchall()
    for ds in dest_data:
        ds["turnover"] = float(ds["turnover"]) if ds["turnover"] else 0.0
        ds["gp"] = float(ds["gp"]) if ds["gp"] else 0.0
        
    cursor.close()
    conn.close()
    
    return jsonify({
        "success": True,
        "monthly": monthly_data,
        "daily": daily_data,
        "airline": airline_data,
        "destination": dest_data
    })


# =========================================================================
# ATL ADMIN API ENDPOINTS
# =========================================================================

# API: Admin General Stats
@app.route("/api/admin/stats")
def api_admin_stats():
    if "user_id" not in session or session["role"] != "admin":
        return jsonify({"success": False, "error": "Unauthorized"}), 401
        
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    
    try:
        # Total Turnover & GP
        cursor.execute("""
            SELECT 
                SUM(b.total_price) as total_turnover,
                SUM(
                    CASE 
                        WHEN b.booking_type = 'flight' THEN fb.service_fee
                        ELSE hb.service_fee
                    END
                ) as total_gp
            FROM bookings b
            LEFT JOIN flight_bookings fb ON b.id = fb.booking_id
            LEFT JOIN hotel_bookings hb ON b.id = hb.booking_id
            WHERE b.status = 'ticketed'
        """)
        totals = cursor.fetchone()
        
        # Segment counts GDS-wise (Amadeus vs Sabre vs LCC vs NDC)
        cursor.execute("""
            SELECT gds_type, COUNT(id) as segments
            FROM flight_bookings
            WHERE ticket_status = 'ticketed'
            GROUP BY gds_type
        """)
        gds_segments = cursor.fetchall()
        
        # Top 5 B2B Agents by Turnover
        cursor.execute("""
            SELECT u.username, u.company_name, u.credit_balance, SUM(b.total_price) as turnover
            FROM bookings b
            JOIN users u ON b.agent_id = u.id
            WHERE b.status = 'ticketed'
            GROUP BY u.id
            ORDER BY turnover DESC
            LIMIT 5
        """)
        top_agents = cursor.fetchall()
        for ag in top_agents:
            ag["credit_balance"] = float(ag["credit_balance"])
            ag["turnover"] = float(ag["turnover"]) if ag["turnover"] else 0.0
            
        # Top 5 Destinations
        cursor.execute("""
            SELECT 
                CASE 
                    WHEN b.booking_type = 'flight' THEN f.destination
                    ELSE h.location
                END as destination,
                COUNT(b.id) as bookings
            FROM bookings b
            LEFT JOIN flight_bookings fb ON b.id = fb.booking_id
            LEFT JOIN flights f ON fb.flight_id = f.id
            LEFT JOIN hotel_bookings hb ON b.id = hb.booking_id
            LEFT JOIN rooms r ON hb.room_id = r.id
            LEFT JOIN hotels h ON r.hotel_id = h.id
            WHERE b.status = 'ticketed'
            GROUP BY destination
            ORDER BY bookings DESC
            LIMIT 5
        """)
        top_destinations = cursor.fetchall()
        
        # Top 5 Airlines
        cursor.execute("""
            SELECT f.airline, COUNT(fb.id) as ticket_count
            FROM flight_bookings fb
            JOIN flights f ON fb.flight_id = f.id
            WHERE fb.ticket_status = 'ticketed'
            GROUP BY f.airline
            ORDER BY ticket_count DESC
            LIMIT 5
        """)
        top_airlines = cursor.fetchall()
        
        # Onboarded agents count
        cursor.execute("SELECT COUNT(id) as cnt FROM users WHERE role = 'agent'")
        total_agents = cursor.fetchone()["cnt"]
        
        # Pending support tickets
        cursor.execute("SELECT COUNT(id) as cnt FROM support_tickets WHERE status = 'open'")
        open_tickets = cursor.fetchone()["cnt"]
        
        cursor.close()
        conn.close()
        
        return jsonify({
            "success": True,
            "total_turnover": float(totals["total_turnover"]) if totals["total_turnover"] else 0.0,
            "total_gp": float(totals["total_gp"]) if totals["total_gp"] else 0.0,
            "gds_segments": gds_segments,
            "top_agents": top_agents,
            "top_destinations": top_destinations,
            "top_airlines": top_airlines,
            "total_agents": total_agents,
            "open_tickets": open_tickets
        })
        
    except Exception as e:
        cursor.close()
        conn.close()
        return jsonify({"success": False, "error": str(e)}), 500

# API: Load Agents List
@app.route("/api/admin/agents/list")
def api_admin_agents_list():
    if "user_id" not in session or session["role"] != "admin":
        return jsonify({"success": False, "error": "Unauthorized"}), 401
        
    agents = query_db("""
        SELECT id, username, email, company_name, phone, credit_balance, onboarded_at 
        FROM users 
        WHERE role = 'agent' 
        ORDER BY onboarded_at DESC
    """)
    for ag in agents:
        ag["credit_balance"] = float(ag["credit_balance"])
        ag["onboarded_at"] = ag["onboarded_at"].isoformat()
    return jsonify({"success": True, "agents": agents})

# API: Admin Load agent info
@app.route("/api/admin/agent/<int:agent_id>")
def api_admin_agent_detail(agent_id):
    if "user_id" not in session or session["role"] != "admin":
        return jsonify({"success": False, "error": "Unauthorized"}), 401
        
    agent = query_db("SELECT id, username, email, company_name, phone, credit_balance FROM users WHERE id = %s", (agent_id,), one=True)
    if agent:
        agent["credit_balance"] = float(agent["credit_balance"])
        return jsonify({"success": True, "agent": agent})
    return jsonify({"success": False, "error": "Agent not found"}), 404

# API: Onboard New Agent (User Registration)
@app.route("/api/admin/agents/onboard", methods=["POST"])
def api_admin_agents_onboard():
    if "user_id" not in session or session["role"] != "admin":
        return jsonify({"success": False, "error": "Unauthorized"}), 401
        
    data = request.json
    username = data.get("username", "").strip()
    password = data.get("password", "").strip()
    email = data.get("email", "").strip()
    company_name = data.get("company_name", "").strip()
    phone = data.get("phone", "").strip()
    initial_credit = data.get("credit_balance", 0.0)
    
    if not username or not password or not email or not company_name:
        return jsonify({"success": False, "error": "Username, password, email, and company name are required."}), 400
        
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        # Check if username exists
        cursor.execute("SELECT id FROM users WHERE username = %s", (username,))
        if cursor.fetchone():
            return jsonify({"success": False, "error": "Username already exists."}), 400
            
        cursor.execute("""
            INSERT INTO users (username, password, email, role, credit_balance, company_name, phone, onboarded_at)
            VALUES (%s, %s, %s, 'agent', %s, %s, %s, NOW())
        """, (username, password, email, Decimal(str(initial_credit)), company_name, phone))
        conn.commit()
        cursor.close()
        conn.close()
        return jsonify({"success": True, "message": "Agent account onboarded and registered successfully!"})
    except Exception as e:
        conn.rollback()
        cursor.close()
        conn.close()
        return jsonify({"success": False, "error": str(e)}), 500

# API: Admin Update Agent Credit Balance
@app.route("/api/admin/agents/update-credit", methods=["POST"])
def api_admin_agents_update_credit():
    if "user_id" not in session or session["role"] != "admin":
        return jsonify({"success": False, "error": "Unauthorized"}), 401
        
    data = request.json
    agent_id = data.get("agent_id")
    amount = data.get("amount") # Can be positive or negative
    description = data.get("description", "Admin credit manual adjustment")
    
    if not agent_id or amount is None:
        return jsonify({"success": False, "error": "Agent ID and Amount are required."}), 400
        
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        # Update balance
        cursor.execute("UPDATE users SET credit_balance = credit_balance + %s WHERE id = %s AND role = 'agent'", (Decimal(str(amount)), agent_id))
        conn.commit()
        
        # Get new balance
        cursor.execute("SELECT credit_balance, company_name FROM users WHERE id = %s", (agent_id,))
        res = cursor.fetchone()
        new_balance = float(res[0])
        company_name = res[1]
        
        cursor.close()
        conn.close()
        return jsonify({
            "success": True, 
            "message": f"Credit adjusted successfully for {company_name}! New Balance: ${new_balance:.2f}",
            "new_balance": new_balance
        })
    except Exception as e:
        conn.rollback()
        cursor.close()
        conn.close()
        return jsonify({"success": False, "error": str(e)}), 500

# API: Load Configured Service Fees
@app.route("/api/admin/fees/list")
def api_admin_fees_list():
    if "user_id" not in session or session["role"] != "admin":
        return jsonify({"success": False, "error": "Unauthorized"}), 401
        
    fees = query_db("SELECT * FROM service_fees")
    for f in fees:
        f["amount"] = float(f["amount"])
    return jsonify({"success": True, "fees": fees})

# API: Update Configured Service Fee
@app.route("/api/admin/fees/update", methods=["POST"])
def api_admin_fees_update():
    if "user_id" not in session or session["role"] != "admin":
        return jsonify({"success": False, "error": "Unauthorized"}), 401
        
    data = request.json
    fee_id = data.get("id")
    amount = data.get("amount")
    fee_type = data.get("fee_type", "markup")
    
    if not fee_id or amount is None or float(amount) < 0:
        return jsonify({"success": False, "error": "Invalid service fee configurations."}), 400
        
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("UPDATE service_fees SET amount = %s, fee_type = %s WHERE id = %s", (Decimal(str(amount)), fee_type, fee_id))
        conn.commit()
        cursor.close()
        conn.close()
        return jsonify({"success": True, "message": "Service fee markup updated successfully! All future transactions will reflect this markup."})
    except Exception as e:
        conn.rollback()
        cursor.close()
        conn.close()
        return jsonify({"success": False, "error": str(e)}), 500

# API: Post Pop-up Message (Alert/Advisory Broadcast)
@app.route("/api/admin/popups/create", methods=["POST"])
def api_admin_popups_create():
    if "user_id" not in session or session["role"] != "admin":
        return jsonify({"success": False, "error": "Unauthorized"}), 401
        
    data = request.json
    message_text = data.get("message_text", "").strip()
    
    if not message_text:
        return jsonify({"success": False, "error": "Alert message cannot be blank."}), 400
        
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        # Deactivate previous popups if they exist, or just insert new active one
        cursor.execute("INSERT INTO popups (message_text, is_active, created_at) VALUES (%s, 1, NOW())", (message_text,))
        conn.commit()
        cursor.close()
        conn.close()
        return jsonify({"success": True, "message": "Pop-up alert broadcasted to all active B2B agents!"})
    except Exception as e:
        conn.rollback()
        cursor.close()
        conn.close()
        return jsonify({"success": False, "error": str(e)}), 500

# API: Support Tickets - Resolve Ticket
@app.route("/api/admin/support/resolve", methods=["POST"])
def api_admin_support_resolve():
    if "user_id" not in session or session["role"] != "admin":
        return jsonify({"success": False, "error": "Unauthorized"}), 401
        
    ticket_id = request.json.get("ticket_id")
    
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("UPDATE support_tickets SET status = 'resolved' WHERE id = %s", (ticket_id,))
        conn.commit()
        cursor.close()
        conn.close()
        return jsonify({"success": True, "message": "Helpdesk ticket resolved successfully!"})
    except Exception as e:
        conn.rollback()
        cursor.close()
        conn.close()
        return jsonify({"success": False, "error": str(e)}), 500


if __name__ == "__main__":
    app.run(debug=True, host="127.0.0.1", port=5000)
