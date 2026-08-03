from flask import Flask, render_template, request, redirect, url_for, session, jsonify
import mysql.connector
from decimal import Decimal
import datetime
import random
import os
import socket
socket.setdefaulttimeout(2.0)
from authlib.integrations.flask_client import OAuth
app = Flask(__name__)
app.secret_key = "travel_portal_secret_key_travelport_b2b"

# Configure OAuth
oauth = OAuth(app)
google = oauth.register(
    name='google',
    client_id=os.environ.get("GOOGLE_CLIENT_ID", "DUMMY_CLIENT_ID"),
    client_secret=os.environ.get("GOOGLE_CLIENT_SECRET", "DUMMY_CLIENT_SECRET"),
    server_metadata_url='https://accounts.google.com/.well-known/openid-configuration',
    client_kwargs={'scope': 'openid email profile'}
)

@app.after_request
def add_header(response):
    response.headers['Cache-Control'] = 'no-store, no-cache, must-revalidate, post-check=0, pre-check=0, max-age=0'
    response.headers['Pragma'] = 'no-cache'
    response.headers['Expires'] = '-1'
    return response

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
            if user.get("status") == "inactive":
                error = "Your account has been deactivated. Please contact support."
            else:
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
    
    # Get active popups (global or specific to this agent)
    popups = query_db("SELECT * FROM popups WHERE is_active = 1 AND (agent_id IS NULL OR agent_id = %s) ORDER BY created_at DESC", (agent_id,))
    
    # Get flight list for search default
    flights = query_db("SELECT * FROM flights ORDER BY price ASC")
    
    # Get hotels list for search default
    hotels = query_db("SELECT * FROM hotels ORDER BY rating DESC")
    
    return render_template("agent_dashboard.html", agent=agent_info, popups=popups, flights=flights, hotels=hotels)

# Route: Flight Results (New Window)
@app.route("/flight-results")
def flight_results():
    if "user_id" not in session or session["role"] != "agent":
        return redirect(url_for("login"))
    
    agent_id = session["user_id"]
    agent_info = query_db("SELECT * FROM users WHERE id = %s", (agent_id,), one=True)
    
    return render_template("flight_results.html", agent=agent_info)

# Route: B2C Home
@app.route("/b2c")
def b2c_home():
    if request.args.get('action') != 'change':
        session.pop('modifying_booking_id', None)
        session.pop('modifying_old_price', None)
    return render_template("b2c_home.html")

# Route: B2C Flight Results
@app.route("/b2c-flight-results")
def b2c_flight_results():
    if request.args.get('modifying') != 'true':
        session.pop('modifying_booking_id', None)
        session.pop('modifying_old_price', None)
    modifying_old_price = session.get('modifying_old_price', 0)
    return render_template("b2c_flight_results.html", agent=None, modifying_old_price=modifying_old_price)

# Route: B2C Hotel Booking Checkout
@app.route("/b2c/hotel-booking")
def b2c_hotel_booking():
    return render_template("b2c_hotel_booking.html")

# Route: B2C Google Sign-In
@app.route("/b2c/login/google")
def b2c_login_google():
    if os.environ.get("GOOGLE_CLIENT_ID") is None or os.environ.get("GOOGLE_CLIENT_ID") == "DUMMY_CLIENT_ID":
        # Simulate OAuth Consent Screen for demo purposes if no API keys are provided
        return render_template("mock_google_login.html")
        
    redirect_uri = url_for('b2c_auth_google_callback', _external=True)
    return google.authorize_redirect(redirect_uri)

# Route: B2C Mock Google Callback (For Testing)
@app.route("/b2c/auth/google/callback/mock", methods=["POST"])
def b2c_mock_google_callback():
    email = request.form.get("email", "demo.traveler@gmail.com")
    name = email.split('@')[0].capitalize()
    
    conn = get_db_connection()
    c = conn.cursor(dictionary=True)
    c.execute("SELECT * FROM b2c_users WHERE email = %s", (email,))
    existing_user = c.fetchone()
    
    if not existing_user:
        c.execute("INSERT INTO b2c_users (email, password, full_name, created_at) VALUES (%s, %s, %s, NOW())", 
                  (email, 'google_sso', name))
        conn.commit()
    conn.close()
    
    session['b2c_user'] = {'email': email, 'name': name}
    return redirect(url_for('b2c_my_bookings'))

# Route: B2C Google Callback
@app.route("/b2c/auth/google/callback")
def b2c_auth_google_callback():
    token = google.authorize_access_token()
    user = google.parse_id_token(token, None)
    
    # Check if user exists in b2c_users, if not create one
    conn = get_db_connection()
    c = conn.cursor(dictionary=True)
    c.execute("SELECT * FROM b2c_users WHERE email = %s", (user['email'],))
    existing_user = c.fetchone()
    
    if not existing_user:
        c.execute("INSERT INTO b2c_users (email, password, full_name, created_at) VALUES (%s, %s, %s, NOW())", 
                  (user['email'], 'google_sso', user.get('name', 'Customer')))
        conn.commit()
    conn.close()
    
    session['b2c_user'] = {'email': user['email'], 'name': user.get('name', 'Customer')}
    return redirect(url_for('b2c_my_bookings'))

# Route: B2C Logout
@app.route("/b2c/logout")
def b2c_logout():
    session.pop('b2c_user', None)
    return redirect(url_for('b2c_home'))

# Route: B2C My Bookings
@app.route("/b2c/my-bookings", methods=["GET", "POST"])
def b2c_my_bookings():
    booking_data = None
    history_data = []
    hotel_history_data = []
    holiday_history_data = []
    price_alerts_data = []
    error = None
    b2c_user = session.get('b2c_user')
    search_email = session.get('b2c_search_email')
    search_mobile = session.get('b2c_search_mobile')
    
    conn = get_db_connection()
    c = conn.cursor(dictionary=True)
    
    emails = set()
    mobiles = set()
    
    if b2c_user:
        emails.add(b2c_user['email'])
    
    if search_email:
        emails.add(search_email)
    if search_mobile:
        mobiles.add(search_mobile)
        
    if request.method == "POST":
        hist_email = request.form.get("hist_email", "").strip()
        hist_mobile = request.form.get("hist_mobile", "").strip()
        
        if not hist_email and not hist_mobile:
            error = "Please provide an Email Address or Mobile Number to view your history."
        else:
            if hist_email:
                emails.add(hist_email)
                session['b2c_search_email'] = hist_email
            if hist_mobile:
                mobiles.add(hist_mobile)
                session['b2c_search_mobile'] = hist_mobile
                
    if (emails or mobiles) and not error:
        try:
            # Step 1: Expand search criteria to automatically sync all related bookings.
            # Find any other emails and mobile numbers linked to current ones in the database.
            flight_where = []
            flight_params = []
            if emails:
                flight_where.append(f"email IN ({', '.join(['%s'] * len(emails))})")
                flight_params.extend(list(emails))
            if mobiles:
                flight_where.append(f"mobile IN ({', '.join(['%s'] * len(mobiles))})")
                flight_params.extend(list(mobiles))
                
            if flight_where:
                c.execute(f"SELECT email, mobile FROM b2c_flight_bookings WHERE {' OR '.join(flight_where)}", tuple(flight_params))
                for row in c.fetchall():
                    if row.get('email'):
                        emails.add(row['email'])
                    if row.get('mobile'):
                        mobiles.add(row['mobile'])
                        
            # Query hotel bookings for expansion as well
            hotel_where = []
            hotel_params = []
            if emails:
                hotel_where.append(f"email IN ({', '.join(['%s'] * len(emails))})")
                hotel_params.extend(list(emails))
            if mobiles:
                hotel_where.append(f"mobile IN ({', '.join(['%s'] * len(mobiles))})")
                hotel_params.extend(list(mobiles))
                
            if hotel_where:
                c.execute(f"SELECT email, mobile FROM b2c_hotel_bookings WHERE {' OR '.join(hotel_where)}", tuple(hotel_params))
                for row in c.fetchall():
                    if row.get('email'):
                        emails.add(row['email'])
                    if row.get('mobile'):
                        mobiles.add(row['mobile'])
            
            # Step 2: Fetch all flights using expanded email & mobile set
            final_flight_where = []
            final_flight_params = []
            if emails:
                final_flight_where.append(f"fb.email IN ({', '.join(['%s'] * len(emails))})")
                final_flight_params.extend(list(emails))
            if mobiles:
                final_flight_where.append(f"fb.mobile IN ({', '.join(['%s'] * len(mobiles))})")
                final_flight_params.extend(list(mobiles))
                
            if final_flight_where:
                flight_query = f"""
                    SELECT DISTINCT fb.id, fb.*, b.status as booking_status, b.total_price, b.invoice_number, b.created_at, f.airline, f.flight_number, f.origin, f.destination, f.departure_time, f.arrival_time
                    FROM b2c_flight_bookings fb
                    JOIN b2c_bookings b ON fb.booking_id = b.id
                    JOIN flights f ON fb.flight_id = f.id
                    WHERE {' OR '.join(final_flight_where)}
                    ORDER BY b.created_at DESC
                """
                c.execute(flight_query, tuple(final_flight_params))
                history_data = c.fetchall()
                
            # Step 3: Fetch all hotels using expanded email & mobile set
            final_hotel_where = []
            final_hotel_params = []
            if emails:
                final_hotel_where.append(f"hb.email IN ({', '.join(['%s'] * len(emails))})")
                final_hotel_params.extend(list(emails))
            if mobiles:
                final_hotel_where.append(f"hb.mobile IN ({', '.join(['%s'] * len(mobiles))})")
                final_hotel_params.extend(list(mobiles))
                
            if final_hotel_where:
                hotel_query = f"""
                    SELECT DISTINCT hb.id, hb.*, b.status as booking_status, b.total_price, b.invoice_number, b.created_at, h.name as hotel_name, h.location as hotel_location, r.room_type
                    FROM b2c_hotel_bookings hb
                    JOIN b2c_bookings b ON hb.booking_id = b.id
                    JOIN rooms r ON hb.room_id = r.id
                    JOIN hotels h ON r.hotel_id = h.id
                    WHERE {' OR '.join(final_hotel_where)}
                    ORDER BY b.created_at DESC
                """
                c.execute(hotel_query, tuple(final_hotel_params))
                hotel_history_data = c.fetchall()

            # Step 4: Fetch all holiday bookings using expanded email & mobile set
            holiday_history_data = []
            final_holiday_where = []
            final_holiday_params = []
            if emails:
                final_holiday_where.append(f"hb.email IN ({', '.join(['%s'] * len(emails))})")
                final_holiday_params.extend(list(emails))
            if mobiles:
                final_holiday_where.append(f"hb.mobile IN ({', '.join(['%s'] * len(mobiles))})")
                final_holiday_params.extend(list(mobiles))
                
            if final_holiday_where:
                holiday_query = f"""
                    SELECT DISTINCT hb.id, hb.*, b.status as booking_status, b.total_price, b.invoice_number, b.created_at
                    FROM b2c_holiday_bookings hb
                    JOIN b2c_bookings b ON hb.booking_id = b.id
                    WHERE {' OR '.join(final_holiday_where)}
                    ORDER BY b.created_at DESC
                """
                c.execute(holiday_query, tuple(final_holiday_params))
                holiday_history_data = c.fetchall()
                
            # Step 5: Fetch price alerts using expanded email & mobile set
            final_alerts_where = []
            final_alerts_params = []
            if emails:
                final_alerts_where.append(f"email IN ({', '.join(['%s'] * len(emails))})")
                final_alerts_params.extend(list(emails))
            if mobiles:
                final_alerts_where.append(f"mobile IN ({', '.join(['%s'] * len(mobiles))})")
                final_alerts_params.extend(list(mobiles))
                
            if final_alerts_where:
                alerts_query = f"""
                    SELECT *
                    FROM b2c_price_alerts
                    WHERE {' OR '.join(final_alerts_where)}
                    ORDER BY created_at DESC
                """
                c.execute(alerts_query, tuple(final_alerts_params))
                price_alerts_data = c.fetchall()
                
            if request.method == "POST" and not history_data and not hotel_history_data and not holiday_history_data and not price_alerts_data:
                error = "No booking history found for the provided details."
                
        except Exception as e:
            error = f"An error occurred while loading history: {str(e)}"
            
    conn.close()
    return render_template("b2c_my_bookings.html", booking_data=None, history_data=history_data, hotel_history_data=hotel_history_data, holiday_history_data=holiday_history_data, price_alerts_data=price_alerts_data, error=error)

# Route: B2C Clear Booking Search Session
@app.route("/b2c/my-bookings/clear")
def b2c_my_bookings_clear():
    session.pop('b2c_search_email', None)
    session.pop('b2c_search_mobile', None)
    return redirect(url_for('b2c_my_bookings'))

# API: Add Price Alert
@app.route("/api/b2c/alerts/add", methods=["POST"])
def api_b2c_alerts_add():
    data = request.json
    email = data.get("email", "").strip()
    mobile = data.get("mobile", "").strip()
    
    destinations = data.get("destination")
    if not destinations:
        return jsonify({"success": False, "error": "Destination is required"}), 400
        
    if isinstance(destinations, str):
        destinations = [destinations]
        
    airline = data.get("airline", "Any Airline").strip()
    notify_email = data.get("notify_email", True)
    notify_sms = data.get("notify_sms", False)
    
    if not email and not mobile:
        return jsonify({"success": False, "error": "Email or mobile is required to save an alert"}), 400
        
    conn = get_db_connection()
    c = conn.cursor()
    try:
        for dest in destinations:
            dest = dest.strip()
            if dest:
                c.execute("""
                    INSERT INTO b2c_price_alerts (email, mobile, destination, airline, notify_email, notify_sms)
                    VALUES (%s, %s, %s, %s, %s, %s)
                """, (email, mobile, dest, airline, notify_email, notify_sms))
        conn.commit()
        
        # Save to session to ensure user sees their alert immediately
        if email: session['b2c_search_email'] = email
        if mobile: session['b2c_search_mobile'] = mobile
            
        return jsonify({"success": True, "message": "Price alert created successfully!"})
    except Exception as e:
        conn.rollback()
        return jsonify({"success": False, "error": str(e)}), 500
    finally:
        c.close()
        conn.close()

# API: Delete Price Alert
@app.route("/api/b2c/alerts/delete", methods=["POST"])
def api_b2c_alerts_delete():
    data = request.json
    alert_id = data.get("id")
    
    if not alert_id:
        return jsonify({"success": False, "error": "Alert ID is required"}), 400
        
    conn = get_db_connection()
    c = conn.cursor()
    try:
        c.execute("DELETE FROM b2c_price_alerts WHERE id = %s", (alert_id,))
        conn.commit()
        return jsonify({"success": True, "message": "Price alert deleted!"})
    except Exception as e:
        conn.rollback()
        return jsonify({"success": False, "error": str(e)}), 500
    finally:
        c.close()
        conn.close()

# Holiday packages static definition
HOLIDAY_PACKAGES = [
    {
        "id": 1,
        "name": "Maldives Group Tour Escape",
        "destination": "Male",
        "country": "Maldives",
        "duration": "4 Days / 3 Nights",
        "hotel": "Kurumba Maldives Resort",
        "hotel_rating": 5,
        "transport": "Speedboat transfers included",
        "price_with_flight": 295000.00,
        "price_without_flight": 175000.00,
        "image": "https://images.unsplash.com/photo-1514282401047-d79a71a590e8?auto=format&fit=crop&q=80&w=800"
    },
    {
        "id": 2,
        "name": "Dubai City & Desert Safari Group Tour",
        "destination": "Dubai",
        "country": "United Arab Emirates (UAE)",
        "duration": "5 Days / 4 Nights",
        "hotel": "Burj Al Arab Jumeirah",
        "hotel_rating": 5,
        "transport": "Private AC Sedan for sightseeing & transfers",
        "price_with_flight": 480000.00,
        "price_without_flight": 320000.00,
        "image": "https://images.unsplash.com/photo-1512453979798-5ea266f8880c?auto=format&fit=crop&q=80&w=800"
    },
    {
        "id": 3,
        "name": "London Heritage & Culture Group Tour",
        "destination": "London",
        "country": "United Kingdom (UK)",
        "duration": "6 Days / 5 Nights",
        "hotel": "Grand Plaza Hotel",
        "hotel_rating": 4,
        "transport": "Airport transfers + Hop-On Hop-Off London Bus pass",
        "price_with_flight": 650000.00,
        "price_without_flight": 410000.00,
        "image": "https://images.unsplash.com/photo-1513635269975-59663e0ca1ad?auto=format&fit=crop&q=80&w=800"
    },
    {
        "id": 4,
        "name": "Singapore Sentosa Adventure Group Tour",
        "destination": "Singapore City",
        "country": "Singapore",
        "duration": "5 Days / 4 Nights",
        "hotel": "Changi Village Inn",
        "hotel_rating": 3,
        "transport": "Airport & activity transfers in private AC Van",
        "price_with_flight": 280000.00,
        "price_without_flight": 160000.00,
        "image": "https://images.unsplash.com/photo-1525625293386-3f8f99389edd?auto=format&fit=crop&q=80&w=800"
    },
    {
        "id": 5,
        "name": "Cultural Triangle & Scenic Sri Lanka Group Tour",
        "destination": "Kandy & Ella",
        "country": "Sri Lanka",
        "duration": "7 Days / 6 Nights",
        "hotel": "Cinnamon Lodge",
        "hotel_rating": 4,
        "transport": "Private AC Micro Van with driver/guide for the entire tour",
        "price_with_flight": 220000.00,
        "price_without_flight": 125000.00,
        "image": "https://images.unsplash.com/photo-1588598126487-dbd2382103f6?auto=format&fit=crop&q=80&w=800"
    }
]

# Route: B2C Holidays
@app.route("/b2c/holidays")
def b2c_holidays():
    return render_template("b2c_holidays.html", packages=HOLIDAY_PACKAGES)

# Route: B2C Offers
@app.route("/b2c/offers")
def b2c_offers():
    return render_template("b2c_offers.html")

# API: Book B2C Holiday Package
@app.route("/api/b2c/holidays/book", methods=["POST"])
def api_b2c_holidays_book():
    data = request.json
    package_id = data.get("package_id")
    guest_name = data.get("guest_name")
    email = data.get("email")
    mobile = data.get("mobile")
    travel_date_str = data.get("travel_date")
    guests_count = int(data.get("guests_count", 1))
    include_flight = bool(data.get("include_flight", True))
    special_requests = data.get("special_requests", "")
    
    if not package_id or not guest_name or not email or not mobile or not travel_date_str:
        return jsonify({"success": False, "error": "All fields are required"}), 400
        
    # Find package
    package = next((p for p in HOLIDAY_PACKAGES if p["id"] == int(package_id)), None)
    if not package:
        return jsonify({"success": False, "error": "Holiday package not found"}), 404
        
    try:
        travel_date = datetime.datetime.strptime(travel_date_str, "%Y-%m-%d").date()
    except ValueError:
        return jsonify({"success": False, "error": "Invalid date format. Use YYYY-MM-DD"}), 400
        
    # Calculate price
    base_price = package["price_with_flight"] if include_flight else package["price_without_flight"]
    total_price = Decimal(str(base_price)) * guests_count
    service_fee = Decimal("1500.00") * guests_count # LKR 1500 per passenger markup
    original_price = total_price - service_fee
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        invoice_number = f"INV-HP{random.randint(100000, 999999)}"
        
        # Insert main booking record
        cursor.execute("""
            INSERT INTO b2c_bookings (booking_type, status, total_price, invoice_number, created_at)
            VALUES ('holiday', 'ticketed', %s, %s, NOW())
        """, (total_price, invoice_number))
        
        booking_id = cursor.lastrowid
        
        # Insert holiday booking details
        cursor.execute("""
            INSERT INTO b2c_holiday_bookings (booking_id, package_name, travel_date, guests_count, include_flight, guest_name, email, mobile, special_requests, original_price, service_fee)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """, (booking_id, package["name"], travel_date, guests_count, include_flight, guest_name, email, mobile, special_requests, original_price, service_fee))
        
        # Store in session to automatically view immediately
        session['b2c_search_email'] = email
        session['b2c_search_mobile'] = mobile
        
        conn.commit()
        cursor.close()
        conn.close()
        
        return jsonify({
            "success": True,
            "message": "Holiday package booked successfully!",
            "invoice_number": invoice_number,
            "total_price": float(total_price)
        })
        
    except Exception as e:
        conn.rollback()
        cursor.close()
        conn.close()
        return jsonify({"success": False, "error": str(e)}), 500

# Route: B2C Self-Service Cancel Booking
@app.route("/b2c/booking/cancel", methods=["POST"])
def b2c_booking_cancel():
    booking_id = request.form.get("booking_id")
    
    if booking_id:
        conn = get_db_connection()
        c = conn.cursor()
        try:
            # Update the main b2c_bookings status to refunded (which represents cancelled/refunded enum value)
            c.execute("UPDATE b2c_bookings SET status = 'refunded' WHERE id = %s", (booking_id,))
            conn.commit()
        except Exception as e:
            print("Error cancelling booking:", e)
        finally:
            conn.close()
            
    return redirect(url_for('b2c_my_bookings'))

# Route: B2C Self-Service Change Date
@app.route("/b2c/booking/change", methods=["POST"])
def b2c_booking_change():
    booking_id = request.form.get("booking_id")
    
    if booking_id:
        conn = get_db_connection()
        c = conn.cursor(dictionary=True)
        try:
            c.execute("SELECT total_price FROM b2c_bookings WHERE id = %s", (booking_id,))
            booking = c.fetchone()
            if booking:
                session['modifying_booking_id'] = booking_id
                session['modifying_old_price'] = float(booking['total_price'])
                return redirect(url_for('b2c_home', action='change'))
        except Exception as e:
            print("Error preparing booking change:", e)
        finally:
            conn.close()
            
    return redirect(url_for('b2c_my_bookings'))

# Route: B2C Cancel Change Request
@app.route("/b2c/booking/cancel-change")
def b2c_booking_cancel_change():
    session.pop('modifying_booking_id', None)
    session.pop('modifying_old_price', None)
    return redirect(url_for('b2c_home'))

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

LOCATION_MAPPING = {
    "SRI LANKA": "CMB",
    "COLOMBO": "CMB",
    "MALDIVES": "MLE",
    "MALE": "MLE",
    "LONDON": "LON",
    "UNITED KINGDOM": "LON",
    "UK": "LON",
    "SINGAPORE": "SIN",
    "DUBAI": "DXB",
    "UAE": "DXB",
    "UNITED ARAB EMIRATES": "DXB",
    "DOHA": "DOH",
    "QATAR": "DOH",
    "SYDNEY": "SYD",
    "AUSTRALIA": "SYD",
    "MELBOURNE": "MEL",
    "NEW YORK": "JFK",
    "USA": "JFK",
    "UNITED STATES": "JFK",
    "DELHI": "DEL",
    "INDIA": "DEL",
    "FRANCE": "CDG",
    "PARIS": "CDG",
    "GERMANY": "FRA",
    "FRANKFURT": "FRA",
    "MUNICH": "MUC",
    "ITALY": "FCO",
    "ROME": "FCO",
    "SWITZERLAND": "ZRH",
    "ZURICH": "ZRH",
    "JAPAN": "HND",
    "TOKYO": "HND",
    "MALAYSIA": "KUL",
    "KUALA LUMPUR": "KUL",
    "THAILAND": "BKK",
    "BANGKOK": "BKK",
    "SAUDI ARABIA": "RUH",
    "RIYADH": "RUH",
    "JEDDAH": "JED",
    "CHINA": "PEK",
    "BEIJING": "PEK",
    "CANADA": "YYZ",
    "TORONTO": "YYZ",
    "JAFFNA": "JAF",
    "CHENNAI": "MAA",
    "MUMBAI": "BOM",
    "BANGALORE": "BLR",
    "NEWARK": "EWR"
}

AIRLINE_MAPPING = {
    "UL": "SriLankan Airlines",
    "EK": "Emirates",
    "QR": "Qatar Airways",
    "SQ": "Singapore Airlines",
    "6E": "IndiGo",
    "BA": "British Airways",
    "EY": "Etihad Airways",
    "WY": "Oman Air",
    "GF": "Gulf Air",
    "AI": "Air India",
    "MH": "Malaysia Airlines",
    "TG": "Thai Airways",
    "TK": "Turkish Airlines",
    "QF": "Qantas",
    "LH": "Lufthansa",
    "CX": "Cathay Pacific",
    "MS": "EgyptAir",
    "FZ": "flydubai",
    "G9": "Air Arabia",
    "CZ": "China Southern Airlines",
    "MU": "China Eastern Airlines",
    "OD": "Batik Air Malaysia",
    "JQ": "Jetstar Airways",
    "W2": "FlexFlight",
    "X1": "Hahn Air Technologies",
    "A1": "Air One"
}

POPULAR_LOCATIONS = [
    {"city": "Colombo", "code": "CMB", "name": "Bandaranaike Intl Arpt", "country": "SRI LANKA", "country_code": "LK"},
    {"city": "Jaffna", "code": "JAF", "name": "Jaffna Intl Arpt", "country": "SRI LANKA", "country_code": "LK"},
    {"city": "Delhi", "code": "DEL", "name": "Delhi Indira Gandhi Intl", "country": "INDIA", "country_code": "IN"},
    {"city": "Chennai", "code": "MAA", "name": "Chennai Arpt", "country": "INDIA", "country_code": "IN"},
    {"city": "Mumbai", "code": "BOM", "name": "Chhatrapati Shivaji Maharaj Intl", "country": "INDIA", "country_code": "IN"},
    {"city": "Bangalore", "code": "BLR", "name": "Kempegowda Intl", "country": "INDIA", "country_code": "IN"},
    {"city": "Singapore", "code": "SIN", "name": "Changi Arpt", "country": "SINGAPORE", "country_code": "SG"},
    {"city": "Male", "code": "MLE", "name": "Velana Intl Arpt", "country": "MALDIVES", "country_code": "MV"},
    {"city": "London", "code": "LHR", "name": "London Heathrow Arpt", "country": "UNITED KINGDOM", "country_code": "GB"},
    {"city": "London", "code": "LGW", "name": "London Gatwick Arpt", "country": "UNITED KINGDOM", "country_code": "GB"},
    {"city": "Dubai", "code": "DXB", "name": "Dubai Intl Arpt", "country": "UNITED ARAB EMIRATES", "country_code": "AE"},
    {"city": "Abu Dhabi", "code": "AUH", "name": "Abu Dhabi Intl Arpt", "country": "UNITED ARAB EMIRATES", "country_code": "AE"},
    {"city": "Doha", "code": "DOH", "name": "Hamad Intl Arpt", "country": "QATAR", "country_code": "QA"},
    {"city": "Sydney", "code": "SYD", "name": "Sydney Kingsford Smith Arpt", "country": "AUSTRALIA", "country_code": "AU"},
    {"city": "Melbourne", "code": "MEL", "name": "Melbourne Arpt", "country": "AUSTRALIA", "country_code": "AU"},
    {"city": "New York", "code": "JFK", "name": "John F. Kennedy Intl", "country": "UNITED STATES", "country_code": "US"},
    {"city": "New York", "code": "LGA", "name": "LaGuardia Arpt", "country": "UNITED STATES", "country_code": "US"},
    {"city": "Newark", "code": "EWR", "name": "Newark Liberty Intl", "country": "UNITED STATES", "country_code": "US"},
    {"city": "Paris", "code": "CDG", "name": "Charles de Gaulle Arpt", "country": "FRANCE", "country_code": "FR"},
    {"city": "Frankfurt", "code": "FRA", "name": "Frankfurt Arpt", "country": "GERMANY", "country_code": "DE"},
    {"city": "Munich", "code": "MUC", "name": "Munich Arpt", "country": "GERMANY", "country_code": "DE"},
    {"city": "Rome", "code": "FCO", "name": "Leonardo da Vinci-Fiumicino Arpt", "country": "ITALY", "country_code": "IT"},
    {"city": "Zurich", "code": "ZRH", "name": "Zurich Arpt", "country": "SWITZERLAND", "country_code": "CH"},
    {"city": "Tokyo", "code": "HND", "name": "Haneda Arpt", "country": "JAPAN", "country_code": "JP"},
    {"city": "Tokyo", "code": "NRT", "name": "Narita Intl Arpt", "country": "JAPAN", "country_code": "JP"},
    {"city": "Kuala Lumpur", "code": "KUL", "name": "Kuala Lumpur Intl", "country": "MALAYSIA", "country_code": "MY"},
    {"city": "Bangkok", "code": "BKK", "name": "Suvarnabhumi Arpt", "country": "THAILAND", "country_code": "TH"},
    {"city": "Riyadh", "code": "RUH", "name": "King Khalid Intl Arpt", "country": "SAUDI ARABIA", "country_code": "SA"},
    {"city": "Jeddah", "code": "JED", "name": "King Abdulaziz Intl Arpt", "country": "SAUDI ARABIA", "country_code": "SA"},
    {"city": "Beijing", "code": "PEK", "name": "Beijing Capital Intl", "country": "CHINA", "country_code": "CN"},
    {"city": "Toronto", "code": "YYZ", "name": "Toronto Pearson Intl", "country": "CANADA", "country_code": "CA"}
]

def get_country_flag(country_code):
    if not country_code or len(country_code) != 2:
        return ""
    try:
        c1, c2 = country_code.upper()
        return chr(127397 + ord(c1)) + chr(127397 + ord(c2))
    except Exception:
        return ""

def resolve_iata_code(keyword, flight_api_client=None):
    if len(keyword) == 3 and keyword.isalpha():
        return keyword.upper()
        
    from services.travelport_service import TravelportService
    tp_service = TravelportService()
    
    try:
        response = tp_service.search_locations(keyword)
        if response["success"] and response.get("data"):
            data = response["data"]
            if isinstance(data, list) and len(data) > 0:
                return data[0].get('iataCode') or data[0].get('address', {}).get('cityCode')
    except Exception as e:
        print(f"Error resolving location '{keyword}':", e)
    return None
        
    # Extract 3-letter code from parentheses if present (e.g., "Colombo, Sri Lanka (CMB)" -> "CMB")
    import re
    match = re.search(r'\(([A-Z]{3})\)', keyword.upper())
    if match:
        return match.group(1)
        
    val = keyword.strip().upper()
    if len(val) == 3 and val.isalpha():
        return val
    # Check local mapping
    if val in LOCATION_MAPPING:
        return LOCATION_MAPPING[val]
    # Fallback to Location Search API
    if flight_api_client:
        try:
            response = flight_api_client.reference_data.locations.get(
                keyword=keyword,
                subType='CITY'
            )
            if response.data:
                return response.data[0].get('iataCode') or response.data[0].get('address', {}).get('cityCode')
        except Exception as e:
            print(f"Error resolving location '{keyword}':", e)
    return None

# API: Autocomplete Search Locations
@app.route("/api/locations/search", methods=["GET"])
def api_locations_search():
    q = request.args.get("q", "").strip().upper()
    
    STATIC_LOCATIONS = [
        {"city": "Colombo", "code": "CMB", "name": "Bandaranaike Intl Arpt", "country": "SRI LANKA", "country_code": "LK"},
        {"city": "Jaffna", "code": "JAF", "name": "Jaffna Intl Arpt", "country": "SRI LANKA", "country_code": "LK"},
        {"city": "Delhi", "code": "DEL", "name": "Indira Gandhi Intl", "country": "INDIA", "country_code": "IN"},
        {"city": "Mumbai", "code": "BOM", "name": "Chhatrapati Shivaji Maharaj Intl", "country": "INDIA", "country_code": "IN"},
        {"city": "Chennai", "code": "MAA", "name": "Chennai Intl", "country": "INDIA", "country_code": "IN"},
        {"city": "Bangalore", "code": "BLR", "name": "Kempegowda Intl", "country": "INDIA", "country_code": "IN"},
        {"city": "Singapore", "code": "SIN", "name": "Changi Arpt", "country": "SINGAPORE", "country_code": "SG"},
        {"city": "Male", "code": "MLE", "name": "Velana Intl Arpt", "country": "MALDIVES", "country_code": "MV"},
        {"city": "London", "code": "LHR", "name": "Heathrow Arpt", "country": "UNITED KINGDOM", "country_code": "GB"},
        {"city": "London", "code": "LGW", "name": "Gatwick Arpt", "country": "UNITED KINGDOM", "country_code": "GB"},
        {"city": "Dubai", "code": "DXB", "name": "Dubai Intl Arpt", "country": "UNITED ARAB EMIRATES", "country_code": "AE"},
        {"city": "Abu Dhabi", "code": "AUH", "name": "Zayed Intl Arpt", "country": "UNITED ARAB EMIRATES", "country_code": "AE"},
        {"city": "Doha", "code": "DOH", "name": "Hamad Intl Arpt", "country": "QATAR", "country_code": "QA"},
        {"city": "Sydney", "code": "SYD", "name": "Kingsford Smith Arpt", "country": "AUSTRALIA", "country_code": "AU"},
        {"city": "Melbourne", "code": "MEL", "name": "Melbourne Arpt", "country": "AUSTRALIA", "country_code": "AU"},
        {"city": "New York", "code": "JFK", "name": "John F. Kennedy Intl", "country": "UNITED STATES", "country_code": "US"},
        {"city": "New York", "code": "LGA", "name": "LaGuardia Arpt", "country": "UNITED STATES", "country_code": "US"},
        {"city": "Los Angeles", "code": "LAX", "name": "Los Angeles Intl", "country": "UNITED STATES", "country_code": "US"},
        {"city": "Paris", "code": "CDG", "name": "Charles de Gaulle Arpt", "country": "FRANCE", "country_code": "FR"},
        {"city": "Frankfurt", "code": "FRA", "name": "Frankfurt Arpt", "country": "GERMANY", "country_code": "DE"},
        {"city": "Rome", "code": "FCO", "name": "Leonardo da Vinci Arpt", "country": "ITALY", "country_code": "IT"},
        {"city": "Zurich", "code": "ZRH", "name": "Zurich Arpt", "country": "SWITZERLAND", "country_code": "CH"},
        {"city": "Tokyo", "code": "HND", "name": "Haneda Arpt", "country": "JAPAN", "country_code": "JP"},
        {"city": "Tokyo", "code": "NRT", "name": "Narita Intl Arpt", "country": "JAPAN", "country_code": "JP"},
        {"city": "Kuala Lumpur", "code": "KUL", "name": "Kuala Lumpur Intl", "country": "MALAYSIA", "country_code": "MY"},
        {"city": "Bangkok", "code": "BKK", "name": "Suvarnabhumi Arpt", "country": "THAILAND", "country_code": "TH"},
        {"city": "Riyadh", "code": "RUH", "name": "King Khalid Intl", "country": "SAUDI ARABIA", "country_code": "SA"},
        {"city": "Jeddah", "code": "JED", "name": "King Abdulaziz Intl", "country": "SAUDI ARABIA", "country_code": "SA"},
        {"city": "Toronto", "code": "YYZ", "name": "Toronto Pearson Intl", "country": "CANADA", "country_code": "CA"},
        {"city": "Beijing", "code": "PEK", "name": "Beijing Capital Intl", "country": "CHINA", "country_code": "CN"}
    ]
    
    matches = []
    
    for loc in STATIC_LOCATIONS:
        if not q or q in loc["code"] or q in loc["city"].upper() or q in loc["country"].upper():
            matches.append(loc)
            
    # Group results by country
    grouped = {}
    for loc in matches:
        country = loc["country"]
        if country not in grouped:
            grouped[country] = {
                "country": country,
                "flag": get_country_flag(loc["country_code"]),
                "locations": []
            }
        grouped[country]["locations"].append({
            "city": loc["city"],
            "code": loc["code"],
            "name": loc["name"]
        })
        
    sorted_groups = []
    countries = sorted(list(grouped.keys()))
    if "SRI LANKA" in countries:
        countries.remove("SRI LANKA")
        countries.insert(0, "SRI LANKA")
        
    for country in countries:
        sorted_groups.append(grouped[country])
        
    return jsonify({"success": True, "groups": sorted_groups})

@app.route("/api/flights/search", methods=["GET"])
def api_flights_search():
    from services.travelport_service import TravelportService
    import re
    
    origin_raw = request.args.get("origin", "").strip().upper()
    dest_raw = request.args.get("destination", "").strip().upper()
    
    orig_match = re.search(r'\(([A-Z]{3})\)', origin_raw)
    origin = orig_match.group(1) if orig_match else origin_raw
    
    dest_match = re.search(r'\(([A-Z]{3})\)', dest_raw)
    destination = dest_match.group(1) if dest_match else dest_raw
    
    date_str = request.args.get("date", "").strip()
    adults = request.args.get("adults", "1").strip()
    
    tp_service = TravelportService()
    response = tp_service.search_flights(origin, destination, date_str, adults=adults)
    
    if not response["success"]:
        return jsonify({"success": False, "error": response.get("error", "Failed to search flights on Travelport API.")})
        
    tp_data = response["data"]
    formatted_flights = []
    
    # Check for the new v11/v12 CatalogProductOfferingsResponse structure
    print("Keys in tp_data app.py:", tp_data.keys() if isinstance(tp_data, dict) else type(tp_data))
    if "CatalogProductOfferingsResponse" in tp_data:
        root = tp_data.get("CatalogProductOfferingsResponse", {})
        offerings = root.get("CatalogProductOfferings", {}).get("CatalogProductOffering", [])
        print("Offerings count:", len(offerings))
        
        # Build flights reference map
        flights_ref_map = {}
        for item in root.get('ReferenceList', []):
            if item.get('@type') == 'ReferenceListFlight':
                for f in item.get('Flight', []):
                    flights_ref_map[f.get('id')] = f
                    
        conn = get_db_connection()
        cursor = conn.cursor()
        
        for idx, offering in enumerate(offerings):
            try:
                # Get price
                best_price_info = offering.get("ProductBrandOptions", [{}])[0].get("ProductBrandOffering", [{}])[0].get("BestCombinablePrice", {})
                total_price_str = best_price_info.get("TotalPrice", "0")
                try:
                    price_lkr = float(total_price_str)
                except ValueError:
                    price_lkr = 0.0
                    
                # Get flight segments
                flight_refs = offering.get("ProductBrandOptions", [{}])[0].get("flightRefs", [])
                segments = []
                for ref in flight_refs:
                    seg = flights_ref_map.get(ref)
                    if seg:
                        segments.append({
                            "carrierCode": seg.get("carrier"),
                            "number": seg.get("number"),
                            "departure": {
                                "at": f"{seg.get('Departure', {}).get('date')}T{seg.get('Departure', {}).get('time')}"
                            },
                            "arrival": {
                                "at": f"{seg.get('Arrival', {}).get('date')}T{seg.get('Arrival', {}).get('time')}"
                            }
                        })
                
                if not segments:
                    continue
                    
                airline = segments[0]["carrierCode"]
                flight_number = f"{segments[0]['carrierCode']}-{segments[0]['number']}"
                dept_time = segments[0]["departure"]["at"].replace('T', ' ')[:19]
                arr_time = segments[-1]["arrival"]["at"].replace('T', ' ')[:19]
                seats_avail = 9
                segment_count = len(segments)
                
                # Travelport Sandbox requires the transactionId, offer id ("o1"), and product ref ("p0")
                offer_id = offering.get("id", "o1")
                transaction_id = tp_data.get("CatalogProductOfferingsResponse", {}).get("transactionId", "")
                
                # Extract product_ref safely
                product_ref = "p0"
                pbo = offering.get("ProductBrandOptions", [])
                if pbo:
                    product_list = pbo[0].get("ProductBrandOffering", [{}])[0].get("Product", [])
                    if product_list:
                        product_ref = product_list[0].get("productRef", "p0")
                
                combined_offer_id = f"{transaction_id}::{offer_id}::{product_ref}" if transaction_id else f"{offer_id}::{product_ref}"
                
                # Save to DB so it can be booked
                cursor.execute("SELECT id FROM flights WHERE flight_number = %s AND departure_time = %s", (flight_number, dept_time))
                row = cursor.fetchone()
                if row:
                    flight_id = row[0]
                    cursor.execute("UPDATE flights SET offer_identifier = %s WHERE id = %s", (combined_offer_id, flight_id))
                else:
                    cursor.execute("""
                        INSERT INTO flights (flight_number, airline, origin, destination, departure_time, arrival_time, price, seats_available, flight_type, segment_count, offer_identifier)
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, 'GDS', %s, %s)
                    """, (flight_number, airline, origin, destination, dept_time, arr_time, price_lkr, seats_avail, segment_count, combined_offer_id))
                    flight_id = cursor.lastrowid
                
                formatted_flights.append({
                "id": flight_id,
                "airline": airline,
                "flight_number": flight_number,
                "origin": origin,
                "destination": destination,
                "departure_time": dept_time,
                "arrival_time": arr_time,
                "price": price_lkr,
                "seats_available": seats_avail,
                "flight_type": "GDS",
                "gds_source": "Travelport",
                "segment_count": segment_count
                })
            except Exception as e:
                print("Error parsing flight:", e)
            
    conn.commit()
    cursor.close()
    conn.close()
            
    return jsonify({
        "success": True,
        "flights": formatted_flights,
        "return_flights": []
    })

@app.route("/api/flights/seat-availability", methods=["POST"])
def api_flights_seat_availability():
    data = request.json
    flight_id = data.get("flight_id")
    
    if not flight_id:
        return jsonify({"success": False, "error": "Flight ID is required"}), 400
        
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute("SELECT * FROM flights WHERE id = %s", (flight_id,))
        flight = cursor.fetchone()
        if not flight:
            return jsonify({"success": False, "error": "Flight not found"}), 404
            
        early_seat_selection = flight["seats_available"] > 0
        seat_charge = 1500 if early_seat_selection else 0
        
        return jsonify({
            "success": True, 
            "early_seat_selection_available": early_seat_selection,
            "seat_charge": seat_charge
        })
    finally:
        cursor.close()
        conn.close()

# API: Flight Booking (with automatic markup application and credit limit validation)
@app.route("/api/flights/book", methods=["POST"])
def api_flights_book():
    data = request.json
    is_b2c = data.get("b2c", False)
    
    if not is_b2c:
        if "user_id" not in session or session["role"] != "agent":
            return jsonify({"success": False, "error": "Unauthorized"}), 401

    flight_id = data.get("flight_id")
    bypass_seat_selection = data.get("bypass_seat_selection", False)
    
    # Parse passengers array if present
    passengers = data.get("passengers")
    passenger_name = data.get("passenger_name")
    
    if passengers:
        if not passenger_name:
            names = []
            for p in passengers:
                p_title = p.get("title", "")
                p_first = p.get("first_name", "")
                p_last = p.get("last_name", "")
                p_name = f"{p_title} {p_first} {p_last}".strip() if (p_title or p_last) else p_first
                names.append(p_name)
            passenger_name = " & ".join(names)
            
    seat_number = data.get("seat_number", "14A")
    passport_number = data.get("passport_number")
    mobile = data.get("mobile")
    email = data.get("email")
    ticket_now = data.get("ticket_now", False) 
    
    if not flight_id or not passenger_name:
        return jsonify({"success": False, "error": "Flight and passenger name are required"}), 400
        
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    
    try:
        cursor.execute("SELECT * FROM flights WHERE id = %s", (flight_id,))
        flight = cursor.fetchone()
        
        if not flight:
            return jsonify({"success": False, "error": "Flight not found"}), 404
            
        # Send full data payload to Travelport for Booking
        from services.travelport_service import TravelportService
        tp_service = TravelportService()
        
        tp_res = tp_service.book_flight(flight_id, passengers or [], offer_identifier=flight.get("offer_identifier"))
        if not tp_res["success"]:
            # If Travelport booking fails, do not create local DB entry
            return jsonify({"success": False, "error": f"Travelport Booking Failed: {tp_res.get('error')}"})
            
        # Retrieve authentic PNR from Travelport response
        tp_pnr = tp_res.get("data", {}).get("ReservationBuildResponse", {}).get("PNR")
        if not tp_pnr:
            return jsonify({"success": False, "error": "Travelport Booking Failed: No PNR returned from GDS."})
        
        # Calculate markup
        markup_amount = 0
        total_price = flight["price"]
        
        if not is_b2c:
            cursor.execute("SELECT * FROM service_fees WHERE transaction_type = 'flight'")
            fees = cursor.fetchall()
            
            for f in fees:
                if f["amount_type"] == "percentage":
                    amt = float(flight["price"]) * (float(f["amount"]) / 100)
                else:
                    amt = float(f["amount"])
                    
                if f["fee_type"] == "markup" or f["fee_type"] == "service_fee":
                    markup_amount += amt
                elif f["fee_type"] == "markdown":
                    markup_amount -= amt
                            
        total_price += markup_amount
        
        # Check credit limit if B2B
        if not is_b2c:
            cursor.execute("SELECT credit_balance FROM users WHERE id = %s", (session["user_id"],))
            agent = cursor.fetchone()
            if not agent:
                return jsonify({"success": False, "error": "Agent not found"}), 404
            
            if ticket_now and agent["credit_balance"] < total_price:
                return jsonify({"success": False, "error": "Insufficient credit balance for immediate ticketing. Reservation will be non-ticketed.", "code": "INSUFFICIENT_CREDIT"}), 400
                
        # Insert Booking
        invoice_num = f"INV-{random.randint(10000, 99999)}"
        status = "ticketed" if ticket_now else "non-ticketed"
        
        if is_b2c:
            status = "pending"
            b2c_user_id = session.get("user_id") if "user_id" in session else None
            cursor.execute("""
                INSERT INTO b2c_bookings (b2c_user_id, booking_type, invoice_number, total_price, status)
                VALUES (%s, 'flight', %s, %s, %s)
            """, (b2c_user_id, invoice_num, total_price, status))
            booking_id = cursor.lastrowid

            cursor.execute("""
                INSERT INTO b2c_flight_bookings (booking_id, flight_id, passenger_name, gds_type, ticket_status, original_price, pnr_reference, passport_number, mobile, email)
                VALUES (%s, %s, %s, 'Travelport', %s, %s, %s, %s, %s, %s)
            """, (booking_id, flight_id, passenger_name, status, total_price, tp_pnr, passport_number, mobile, email))
            
            return jsonify({
                "success": True, 
                "pnr": tp_pnr,
                "booking_id": booking_id,
                "invoice_number": invoice_num,
                "total_price": total_price,
                "status": status,
                "message": f"B2C Reservation saved via Travelport with PNR {tp_pnr}"
            })
            
        else:
            cursor.execute("""
                INSERT INTO bookings (agent_id, booking_type, invoice_number, total_price, status)
                VALUES (%s, 'flight', %s, %s, %s)
            """, (session["user_id"], invoice_num, total_price, status))
            
            booking_id = cursor.lastrowid
            
            tkt_status = "ticketed" if ticket_now else "non-ticketed"
            tkt_number = tp_res.get("ticket_number") if ticket_now else None
            
            cursor.execute("""
                INSERT INTO flight_bookings (booking_id, flight_id, pnr_reference, passenger_name, seat_number, ticket_status, ticket_number)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
            """, (booking_id, flight_id, tp_pnr, passenger_name, seat_number, tkt_status, tkt_number))
            
            if ticket_now:
                cursor.execute("UPDATE users SET credit_balance = credit_balance - %s WHERE id = %s", (total_price, session["user_id"]))
                cursor.execute("UPDATE flights SET seats_available = seats_available - 1 WHERE id = %s", (flight_id,))
                
            conn.commit()
            
            return jsonify({
                "success": True, 
                "pnr": tp_pnr,
                "booking_id": booking_id,
                "invoice_number": invoice_num,
                "total_price": total_price,
                "status": status,
                "message": f"Reservation successful via Travelport with PNR {tp_pnr}"
            })
            
    except Exception as e:
        conn.rollback()
        return jsonify({"success": False, "error": str(e)}), 500
    finally:
        cursor.close()
        conn.close()

@app.route("/api/flights/issue-ticket", methods=["POST"])
def api_flights_issue_ticket():
    if "user_id" not in session or session["role"] != "agent":
        return jsonify({"success": False, "error": "Unauthorized"}), 401
        
    data = request.json
    booking_id = data.get("booking_id")
    
    if not booking_id:
        return jsonify({"success": False, "error": "Booking ID is required"}), 400
        
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    
    try:
        # Check booking
        cursor.execute("""
            SELECT b.id, b.total_price, b.status, fb.ticket_status, fb.flight_id, fb.pnr_reference 
            FROM bookings b 
            JOIN flight_bookings fb ON b.id = fb.booking_id 
            WHERE b.id = %s AND b.agent_id = %s
        """, (booking_id, session["user_id"]))
        booking = cursor.fetchone()
        
        if not booking:
            return jsonify({"success": False, "error": "Booking not found"}), 404
            
        if booking["ticket_status"] == "ticketed":
            return jsonify({"success": False, "error": "Ticket already issued"}), 400
            
        # Check credit balance
        cursor.execute("SELECT credit_balance FROM users WHERE id = %s", (session["user_id"],))
        agent = cursor.fetchone()
        total_price = booking["total_price"]
        
        if agent["credit_balance"] < total_price:
            return jsonify({"success": False, "error": "Insufficient credit balance to issue ticket."}), 400
            

        # Hit the GDS to issue ticket
        from services.travelport_service import TravelportService
        tp_service = TravelportService()
        pnr = booking.get("pnr_reference")
        
        if pnr:
            tp_res = tp_service.issue_ticket(pnr)
            if tp_res.get("success"):
                tkt_number = tp_res.get("ticket_number")
            else:
                return jsonify({"success": False, "error": "GDS Ticketing Failed: " + tp_res.get("error", "Unknown error")}), 400
        else:
            return jsonify({"success": False, "error": "GDS Ticketing Failed: Booking has no PNR reference"}), 400

        cursor.execute("UPDATE users SET credit_balance = credit_balance - %s WHERE id = %s", (total_price, session["user_id"]))
        cursor.execute("UPDATE bookings SET status = 'ticketed' WHERE id = %s", (booking_id,))
        cursor.execute("UPDATE flight_bookings SET ticket_status = 'ticketed', ticket_number = %s WHERE booking_id = %s", (tkt_number, booking_id))
        cursor.execute("UPDATE flights SET seats_available = seats_available - 1 WHERE id = %s", (booking["flight_id"],))
        
        conn.commit()
        return jsonify({"success": True, "message": "Ticket issued successfully!", "ticket_number": tkt_number})
        
    except Exception as e:
        conn.rollback()
        return jsonify({"success": False, "error": str(e)}), 500
    finally:
        cursor.close()
        conn.close()

@app.route("/api/hotels/search", methods=["GET"])
def api_hotels_search():
    location = request.args.get("location", "").strip()
    
    city_code = location.upper() if len(location) == 3 else None
    
    from services.travelport_service import TravelportService
    tp_service = TravelportService()
    
    if not city_code and len(location) > 2:
        loc_res = tp_service.search_locations(location)
        if loc_res["success"] and loc_res.get("data"):
            city_code = loc_res["data"][0].get("address", {}).get("cityCode")
            
    if not city_code:
        return jsonify({"success": True, "hotels": []})
        
    tp_res = tp_service.search_hotels(city_code)
    
    if not tp_res["success"]:
        return jsonify({"success": False, "error": tp_res.get("error", "Failed to retrieve hotels")})
        
    # Assuming Travelport returns standard hotel structure
    tp_hotels = tp_res.get("data", {}).get("HotelSearchResult", [])
    
    formatted_hotels = []
    for h in tp_hotels:
        hotel_name = h.get("HotelProperty", {}).get("Name", "Unknown Hotel")
        formatted_hotels.append({
            "name": hotel_name,
            "location": f"{city_code}",
            "price_per_night": 150.00, # Mock price since exact structure is unknown
            "rating": 4,
            "image_url": "https://images.unsplash.com/photo-1566073771259-6a8506099945?w=500&auto=format"
        })
        
    return jsonify({"success": True, "hotels": formatted_hotels})

@app.route("/api/pnr/retrieve", methods=["GET"])
def api_pnr_retrieve():
    if "user_id" not in session:
        return jsonify({"success": False, "error": "Unauthorized"}), 401
        
    pnr_code = request.args.get("pnr", "").strip().upper()
    if not pnr_code:
        return jsonify({"success": False, "error": "PNR Reference code is required"}), 400
        
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    
    try:
        # Search B2B
        cursor.execute("""
            SELECT fb.*, f.flight_number, f.airline, f.origin, f.destination, f.departure_time, f.arrival_time, f.flight_type, f.gds_source,
                   b.invoice_number, b.created_at, b.status AS booking_status, b.total_price,
                   u.username AS agent_username, u.company_name AS agent_company
            FROM flight_bookings fb
            JOIN flights f ON fb.flight_id = f.id
            JOIN bookings b ON fb.booking_id = b.id
            LEFT JOIN users u ON b.agent_id = u.id
            WHERE fb.pnr_reference = %s
        """, (pnr_code,))
        b2b_records = cursor.fetchall()
        
        if b2b_records:
            # Format fields
            for r in b2b_records:
                r["original_price"] = float(r["original_price"])
                r["service_fee"] = float(r["service_fee"])
                r["total_price"] = float(r["total_price"])
                r["created_at"] = r["created_at"].isoformat()
                r["departure_time"] = r["departure_time"].isoformat()
                r["arrival_time"] = r["arrival_time"].isoformat()
                
            api_status_msg = "Unknown"
            try:
                from services.travelport_service import TravelportService
                tp = TravelportService()
                api_res = tp.retrieve_pnr(pnr_code)
                if api_res.get("success"):
                    api_status_msg = api_res.get("data", {}).get("Status", "Unknown")
            except Exception as e:
                api_status_msg = "Error reaching GDS"
                
            return jsonify({
                "success": True,
                "source": "B2B",
                "pnr": pnr_code,
                "records": b2b_records,
                "api_status": api_status_msg
            })
            
        # Search B2C
        cursor.execute("""
            SELECT fb.*, f.flight_number, f.airline, f.origin, f.destination, f.departure_time, f.arrival_time, f.flight_type, f.gds_source,
                   b.invoice_number, b.created_at, b.status AS booking_status, b.total_price,
                   u.email AS user_email, u.full_name AS user_fullname
            FROM b2c_flight_bookings fb
            JOIN flights f ON fb.flight_id = f.id
            JOIN b2c_bookings b ON fb.booking_id = b.id
            LEFT JOIN b2c_users u ON b.b2c_user_id = u.id
            WHERE fb.pnr_reference = %s
        """, (pnr_code,))
        b2c_records = cursor.fetchall()
        
        if b2c_records:
            # Format fields
            for r in b2c_records:
                r["original_price"] = float(r["original_price"])
                r["service_fee"] = float(r["service_fee"])
                r["total_price"] = float(r["total_price"])
                r["created_at"] = r["created_at"].isoformat()
                r["departure_time"] = r["departure_time"].isoformat()
                r["arrival_time"] = r["arrival_time"].isoformat()
                
            api_status_msg = "Unknown"
            try:
                from services.travelport_service import TravelportService
                tp = TravelportService()
                api_res = tp.retrieve_pnr(pnr_code)
                if api_res.get("success"):
                    api_status_msg = api_res.get("data", {}).get("Status", "Unknown")
            except Exception as e:
                api_status_msg = "Error reaching GDS"
                
            return jsonify({
                "success": True,
                "source": "B2C",
                "pnr": pnr_code,
                "records": b2c_records,
                "api_status": api_status_msg
            })
            
        return jsonify({"success": False, "error": "PNR not found in any ticketing channel"}), 404
        
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500
    finally:
        cursor.close()
        conn.close()

@app.route("/api/bookings/list")
def api_bookings_list():
    if "user_id" not in session or session["role"] != "agent":
        return jsonify({"success": False, "error": "Unauthorized"}), 401
        
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    
    try:
        cursor.execute("SELECT id, booking_type, invoice_number, status, total_price, created_at FROM bookings WHERE agent_id = %s ORDER BY created_at DESC", (session["user_id"],))
        bookings = cursor.fetchall()
        
        for b in bookings:
            b["total_price"] = float(b["total_price"])
            b["created_at"] = b["created_at"].isoformat() if b["created_at"] else ""
            
            if b["booking_type"] == "flight":
                cursor.execute("""
                    SELECT fb.*, f.airline, f.flight_number, f.origin, f.destination 
                    FROM flight_bookings fb 
                    JOIN flights f ON fb.flight_id = f.id 
                    WHERE fb.booking_id = %s
                """, (b["id"],))
                fbs = cursor.fetchall()
                if fbs:
                    flight_details = fbs[0]
                    b["details"] = {
                        "pnr_reference": flight_details.get("pnr_reference"),
                        "ticket_number": flight_details.get("ticket_number"),
                        "airline": flight_details.get("airline"),
                        "flight_number": flight_details.get("flight_number"),
                        "gds_type": flight_details.get("gds_type"),
                        "origin": flight_details.get("origin"),
                        "destination": flight_details.get("destination"),
                        "seat_number": flight_details.get("seat_number"),
                        "passenger_name": flight_details.get("passenger_name"),
                        "flight_id": flight_details.get("flight_id"),
                        "original_price": float(flight_details.get("original_price") or 0)
                    }
                    if len(fbs) > 1:
                        ret_details = fbs[1]
                        b["details"]["return_segment"] = {
                            "pnr_reference": ret_details.get("pnr_reference"),
                            "ticket_number": ret_details.get("ticket_number"),
                            "airline": ret_details.get("airline"),
                            "flight_number": ret_details.get("flight_number"),
                            "gds_type": ret_details.get("gds_type"),
                            "origin": ret_details.get("origin"),
                            "destination": ret_details.get("destination"),
                            "seat_number": ret_details.get("seat_number")
                        }
            elif b["booking_type"] == "hotel":
                cursor.execute("""
                    SELECT hb.*, r.room_type, h.name as hotel_name 
                    FROM hotel_bookings hb
                    JOIN rooms r ON hb.room_id = r.id
                    JOIN hotels h ON r.hotel_id = h.id
                    WHERE hb.booking_id = %s
                """, (b["id"],))
                hotel_details = cursor.fetchone()
                if hotel_details:
                    b["details"] = {
                        "hotel_name": hotel_details.get("hotel_name", "Unknown Hotel"),
                        "room_type": hotel_details.get("room_type", "Standard"),
                        "check_in": hotel_details.get("check_in", "").isoformat() if hasattr(hotel_details.get("check_in"), "isoformat") else str(hotel_details.get("check_in")),
                        "guest_name": hotel_details.get("guest_name")
                    }
                    
        return jsonify({"success": True, "bookings": bookings})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500
    finally:
        cursor.close()
        conn.close()

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
            
        # Select and ticket all segments via Travelport
        cursor.execute("SELECT id, flight_id, pnr_reference FROM flight_bookings WHERE booking_id = %s", (booking_id,))
        segments = cursor.fetchall()
        
        from services.travelport_service import TravelportService
        tp_service = TravelportService()
        
        for seg in segments:
            pnr = seg.get("pnr_reference", "UNKNOWN")
            tp_res = tp_service.issue_ticket(pnr)
            if not tp_res["success"]:
                # If ticketing fails with Travelport, abort and rollback
                conn.rollback()
                return jsonify({"success": False, "error": f"Travelport ticketing failed for PNR {pnr}: {tp_res.get('error')}"})
            
            tkt_num = tp_res.get("ticket_number", tp_res.get("data", {}).get("TicketNumber"))
            
            cursor.execute("UPDATE flight_bookings SET ticket_status = 'ticketed', ticket_number = %s WHERE id = %s", (tkt_num, seg["id"]))
            cursor.execute("UPDATE flights SET seats_available = seats_available - 1 WHERE id = %s", (seg["flight_id"],))
            
        # Update status
        cursor.execute("UPDATE bookings SET status = 'ticketed' WHERE id = %s", (booking_id,))
        
        # Deduct credit
        cursor.execute("UPDATE users SET credit_balance = credit_balance - %s WHERE id = %s", (total_price, session["user_id"]))
        
        # Award loyalty points
        reward_points = int(total_price / 10)
        cursor.execute("""
            INSERT INTO agent_rewards (agent_id, reward_points, description)
            VALUES (%s, %s, %s)
        """, (session["user_id"], reward_points, f"Points earned for ticket issuance {booking['invoice_number']}"))
        
        conn.commit()
        return jsonify({"success": True, "message": "Reservation ticketed successfully via Travelport API! Balance updated."})
        
    except Exception as e:
        conn.rollback()
        return jsonify({"success": False, "error": str(e)}), 500
    finally:
        cursor.close()
        conn.close()

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
        
        # Global Penalty Notifier Logic
        # Let's say penalty is 10% of old flight cost or flat $50
        airline_cancellation_penalty = Decimal("50.00")
        
        old_price = curr_booking["original_price"]
        new_price = new_flight["price"]
        fare_difference = max(Decimal("0.00"), new_price - old_price)
        
        total_reissue_cost = airline_cancellation_penalty + fare_difference + reissue_markup
        
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
                "airline_cancellation_penalty": float(airline_cancellation_penalty),
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
        
        # Airline penalty (typically flat $75 for refunds)
        airline_cancellation_penalty = Decimal("75.00")
        
        original_price = booking["total_price"]
        
        # Calculated refund value: original paid price minus Airline penalty and minus our refund processing fee
        refund_amount = original_price - airline_cancellation_penalty - refund_markup
        
        if refund_amount < 0:
            refund_amount = Decimal("0.00")
            
        # Update booking status to refunded
        cursor.execute("UPDATE bookings SET status = 'refunded' WHERE id = %s", (booking_id,))
        
        if booking["booking_type"] == "flight":
            cursor.execute("UPDATE flight_bookings SET ticket_status = 'refunded' WHERE booking_id = %s", (booking_id,))
            # Restore flight seats for all segments
            cursor.execute("SELECT flight_id FROM flight_bookings WHERE booking_id = %s", (booking_id,))
            segments = cursor.fetchall()
            for seg in segments:
                cursor.execute("UPDATE flights SET seats_available = seats_available + 1 WHERE id = %s", (seg["flight_id"],))
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
                "airline_cancellation_penalty": float(airline_cancellation_penalty),
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
    # Show lowest fare available per destination, airline and flight number
    fares = query_db("""
        SELECT origin, destination, airline, flight_number, MIN(price) as lowest_fare, flight_type
        FROM flights
        GROUP BY origin, destination, airline, flight_number, flight_type
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
        
        # Segment counts GDS-wise (Global vs Sabre vs LCC vs NDC)
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
        SELECT id, username, email, company_name, phone, credit_balance, onboarded_at, status 
        FROM users 
        WHERE role = 'agent' 
        ORDER BY onboarded_at DESC
    """)
    for ag in agents:
        ag["credit_balance"] = float(ag["credit_balance"])
        ag["onboarded_at"] = ag["onboarded_at"].isoformat()
    return jsonify({"success": True, "agents": agents})

# API: Toggle Agent Status
@app.route("/api/admin/agents/toggle-status", methods=["POST"])
def api_admin_agents_toggle_status():
    if "user_id" not in session or session["role"] != "admin":
        return jsonify({"success": False, "error": "Unauthorized"}), 401
        
    data = request.json
    agent_id = data.get("agent_id")
    status = data.get("status")
    
    if not agent_id or status not in ['active', 'inactive']:
        return jsonify({"success": False, "error": "Invalid data."}), 400
        
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("UPDATE users SET status = %s WHERE id = %s AND role = 'agent'", (status, agent_id))
        conn.commit()
        cursor.close()
        conn.close()
        return jsonify({"success": True, "message": f"Agent status updated to {status}."})
    except Exception as e:
        conn.rollback()
        cursor.close()
        conn.close()
        return jsonify({"success": False, "error": str(e)}), 500

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
    currency = data.get("currency", "USD")
    
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
            INSERT INTO users (username, password, email, role, credit_balance, company_name, phone, onboarded_at, currency)
            VALUES (%s, %s, %s, 'agent', %s, %s, %s, NOW(), %s)
        """, (username, password, email, Decimal(str(initial_credit)), company_name, phone, currency))
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
        
        # Generate popup notification for the agent
        amt_float = float(amount)
        action_text = "added to" if amt_float > 0 else "deducted from"
        message_text = f"Credit Update: ${abs(amt_float):.2f} has been {action_text} your account wallet. New Balance: ${new_balance:.2f}. Reason: {description}"
        cursor.execute("INSERT INTO popups (message_text, is_active, created_at, agent_id) VALUES (%s, 1, NOW(), %s)", (message_text, agent_id))
        conn.commit()
        
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
    amount_type = data.get("amount_type", "fixed")
    currency = data.get("currency", "USD")
    
    if not fee_id or amount is None or float(amount) < 0:
        return jsonify({"success": False, "error": "Invalid service fee configurations."}), 400
        
    if amount_type not in ["fixed", "percentage"]:
        return jsonify({"success": False, "error": "Invalid amount type."}), 400
        
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("UPDATE service_fees SET amount = %s, fee_type = %s, amount_type = %s, currency = %s WHERE id = %s", (Decimal(str(amount)), fee_type, amount_type, currency, fee_id))
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

# API: Get Current Agent Credit Balance
@app.route("/api/agent/credit")
def api_agent_credit():
    if "user_id" not in session:
        return jsonify({"success": False, "error": "Unauthorized"}), 401
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute("SELECT credit_balance, company_name FROM users WHERE id = %s", (session["user_id"],))
        agent = cursor.fetchone()
        cursor.close()
        conn.close()
        if agent:
            return jsonify({
                "success": True, 
                "credit_balance": float(agent["credit_balance"]),
                "company_name": agent["company_name"]
            })
        return jsonify({"success": False, "error": "Agent not found"}), 404
    except Exception as e:
        if cursor:
            cursor.close()
        if conn:
            conn.close()
        return jsonify({"success": False, "error": str(e)}), 500

# --- B2C AI Chatbot API ---
@app.route("/api/chatbot/ask", methods=["POST"])
def chatbot_ask():
    data = request.get_json()
    msg = data.get("message", "").lower()
    
    chat_state = session.get('chat_state', None)
    
    if "cancel" in msg or "stop" in msg or "nevermind" in msg:
        session.pop('chat_state', None)
        return jsonify({"reply": "Okay, I've cancelled the current request. How else can I help you today?"})
        
    if chat_state == 'awaiting_origin':
        session['chat_origin'] = msg.upper()
        session['chat_state'] = 'awaiting_dest'
        return jsonify({"reply": f"Great. You are flying from {msg.upper()}. Where are you traveling to? (e.g. MLE, DXB)"})
        
    elif chat_state == 'awaiting_dest':
        session['chat_dest'] = msg.upper()
        session['chat_state'] = 'awaiting_date'
        return jsonify({"reply": f"Got it, destination {msg.upper()}. What date do you want to depart? (Format: YYYY-MM-DD)"})
        
    elif chat_state == 'awaiting_date':
        origin = session.get('chat_origin', 'CMB')
        dest = session.get('chat_dest', 'MLE')
        date = msg
        
        session.pop('chat_state', None)
        session.pop('chat_origin', None)
        session.pop('chat_dest', None)
        
        # Generate dynamic HTML for the flight card directly in the chat
        import random
        price = "{:,.2f}".format(round(random.uniform(35000, 150000), 2))
        
        flight_html = f"""
        <div style='background: white; border: 1px solid #e2e8f0; border-radius: 12px; padding: 18px; margin-top: 15px; box-shadow: 0 4px 12px rgba(0,0,0,0.05); font-family: "Outfit", sans-serif; color: #1e293b; text-align: left;'>
            <div style='font-weight: 800; color: #ac031c; font-size: 15px; margin-bottom: 8px;'><i class='fa-solid fa-plane-departure'></i> Best Flight Found</div>
            <div style='display: flex; justify-content: space-between; align-items: center; margin-bottom: 12px;'>
                <div>
                    <div style='font-size: 18px; font-weight: 700;'>{origin}</div>
                    <div style='font-size: 11px; color: #64748b;'>Origin</div>
                </div>
                <div style='color: #94a3b8;'><i class='fa-solid fa-arrow-right'></i></div>
                <div style='text-align: right;'>
                    <div style='font-size: 18px; font-weight: 700;'>{dest}</div>
                    <div style='font-size: 11px; color: #64748b;'>Destination</div>
                </div>
            </div>
            <div style='font-size: 13px; color: #475569; margin-bottom: 5px;'><i class='fa-regular fa-calendar'></i> <strong>{date}</strong></div>
            <div style='font-size: 18px; font-weight: 800; color: #10b981; margin-bottom: 12px;'>LKR {price}</div>
            <a href='/b2c-flight-results?origin={origin}&dest={dest}&date={date}&adults=1' style='display: block; text-align: center; background: #c3122e; color: white; padding: 10px; border-radius: 8px; text-decoration: none; font-size: 14px; font-weight: bold; transition: background 0.3s;'>Book This Flight Now</a>
        </div>
        """
        return jsonify({"reply": f"I've searched our real-time inventory and found a great option for you! {flight_html}"})
    
    reply = "I'm your Aeronexa AI assistant! You can ask me about baggage allowances, checking in, cancellations, and flight status."
    
    if "baggage" in msg or "luggage" in msg:
        reply = "For Economy class, you are generally allowed 1 checked bag (up to 23kg) and 1 carry-on bag (up to 7kg). Premium classes include additional baggage allowance."
    elif "cancel" in msg or "refund" in msg:
        reply = "You can cancel or change your flights directly from the 'My Bookings' page! If your fare rules allow a refund, it will be automatically processed."
    elif "check in" in msg or "check-in" in msg:
        reply = "Online check-in opens 48 hours before departure. You can check in directly through the Aeronexa portal or at the airport kiosks."
    elif "contact" in msg or "support" in msg:
        reply = "Our customer support team is available 24/7! You can reach us at support@aeronexa.com or call our hotline at +94 11 234 5678."
    elif "hi" in msg or "hello" in msg or "hey" in msg:
        reply = "Hello there! 👋 I'm the Aeronexa AI. How can I help make your journey smoother today?"
    elif "book" in msg or "search" in msg or "flight" in msg:
        session['chat_state'] = 'awaiting_origin'
        reply = "I can definitely help you search for a flight right here! What city or airport code are you flying **FROM**? (e.g. CMB, LHR, DXB)"
    elif "price" in msg or "cost" in msg or "cheap" in msg:
        reply = "We offer the most competitive fares across 500+ airlines! Tell me you want to 'search flights' to see available pricing."
    elif "aeronexa" in msg:
        reply = "Aeronexa is the #1 Travel Booking Platform, designed to give you a premium booking experience from start to finish."
        
    import time
    time.sleep(1) # Simulate AI thinking time
    
    return jsonify({"reply": reply})


# Route: B2C Hotel Details
@app.route("/b2c/hotel-details")
def b2c_hotel_details():
    return render_template("b2c_hotel_details.html")

# Route: B2B Hotel Details
@app.route("/hotel-details")
def b2b_hotel_details():
    if "user_id" not in session or session["role"] != "agent":
        return redirect(url_for("login"))
    
    agent_id = session["user_id"]
    agent_info = query_db("SELECT * FROM users WHERE id = %s", (agent_id,), one=True)
        
    return render_template("hotel_details.html", agent=agent_info)

# Route: B2B Hotel Booking Checkout
@app.route("/hotel-booking")
def b2b_hotel_booking():
    if "user_id" not in session or session["role"] != "agent":
        return redirect(url_for("login"))
        
    agent_id = session["user_id"]
    agent_info = query_db("SELECT * FROM users WHERE id = %s", (agent_id,), one=True)
        
    return render_template("hotel_booking.html", agent=agent_info)


# ==========================================
# B2C ADMIN PORTAL APIS
# ==========================================

@app.route("/api/admin/b2c/users")
def api_admin_b2c_users():
    if "user_id" not in session or session.get("role") not in ["admin", "b2c_admin"]:
        return jsonify({"success": False, "error": "Unauthorized"}), 401
    users = query_db("SELECT id, username, email, phone, registered_at FROM b2c_users ORDER BY registered_at DESC")
    for u in users:
        u["registered_at"] = u["registered_at"].isoformat() if u["registered_at"] else ""
    return jsonify({"success": True, "users": users})

@app.route("/api/admin/b2c/fees/list")
def api_admin_b2c_fees_list():
    if "user_id" not in session or session.get("role") not in ["admin", "b2c_admin"]:
        return jsonify({"success": False, "error": "Unauthorized"}), 401
    fees = query_db("SELECT * FROM b2c_service_fees")
    for f in fees:
        f["amount"] = float(f["amount"])
    return jsonify({"success": True, "fees": fees})

@app.route("/api/admin/b2c/fees/update", methods=["POST"])
def api_admin_b2c_fees_update():
    if "user_id" not in session or session.get("role") not in ["admin", "b2c_admin"]:
        return jsonify({"success": False, "error": "Unauthorized"}), 401
    data = request.json
    fee_id = data.get("id")
    amount = data.get("amount")
    amount_type = data.get("amount_type")
    currency = data.get("currency", "USD")
    if not fee_id or amount is None or amount_type not in ["fixed", "percentage"]:
        return jsonify({"success": False, "error": "Invalid parameters"}), 400
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("UPDATE b2c_service_fees SET amount = %s, amount_type = %s, currency = %s WHERE id = %s", (amount, amount_type, currency, fee_id))
        conn.commit()
        return jsonify({"success": True, "message": "B2C Fee updated successfully."})
    except Exception as e:
        conn.rollback()
        return jsonify({"success": False, "error": str(e)}), 500
    finally:
        cursor.close()
        conn.close()

@app.route("/api/admin/b2c/bookings")
def api_admin_b2c_bookings():
    if "user_id" not in session or session.get("role") not in ["admin", "b2c_admin"]:
        return jsonify({"success": False, "error": "Unauthorized"}), 401
    bookings = query_db("SELECT id, b2c_user_id, pnr, total_price, status, created_at FROM b2c_flight_bookings ORDER BY created_at DESC LIMIT 50")
    for b in bookings:
        b["total_price"] = float(b["total_price"])
        b["created_at"] = b["created_at"].isoformat() if b["created_at"] else ""
    return jsonify({"success": True, "bookings": bookings})


@app.route("/b2c/admin/login", methods=["GET", "POST"])
def b2c_admin_login():
    error = None
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")
        
        user = query_db("SELECT * FROM users WHERE username = %s AND password = %s AND role = 'b2c_admin'", (username, password), one=True)
        if user:
            if user.get("status") == "inactive":
                error = "Your account has been deactivated. Please contact support."
            else:
                session["user_id"] = user["id"]
                session["username"] = user["username"]
                session["role"] = user["role"]
                session["company_name"] = user["company_name"]
                
                return redirect(url_for("b2c_admin_dashboard"))
        else:
            error = "Invalid username or password for B2C Admin."
            
    return render_template("b2c_admin_login.html", error=error)

@app.route("/b2c/admin")
def b2c_admin_dashboard():
    if "user_id" not in session or session.get("role") != "b2c_admin":
        return redirect(url_for("b2c_admin_login"))
        
    admin_info = query_db("SELECT * FROM users WHERE id = %s", (session["user_id"],), one=True)
    return render_template("b2c_admin_dashboard.html", admin=admin_info)



@app.route("/b2c/admin/logout")
def b2c_admin_logout():
    session.clear()
    return redirect(url_for("b2c_admin_login"))

@app.route('/booking-confirmation/<int:booking_id>')
def booking_confirmation(booking_id):
    if session.get('role') not in ('agent', 'premium_agent', 'admin'):
        return redirect(url_for('index'))
        
    db = get_db_connection()
    cursor = db.cursor(dictionary=True)
    
    # Get booking details
    cursor.execute('''
        SELECT b.*, fb.flight_id, fb.pnr_reference, fb.passenger_name, fb.seat_number, 
               fb.ticket_status, fb.ticket_number,
               f.airline, f.flight_number, f.origin, f.destination, 
               f.departure_time, f.arrival_time, f.price,
               f.id as fid
        FROM bookings b
        JOIN flight_bookings fb ON b.id = fb.booking_id
        JOIN flights f ON fb.flight_id = f.id
        WHERE b.id = %s AND b.agent_id = %s
    ''', (booking_id, session['user_id']))
    booking = cursor.fetchone()
    
    if not booking:
        return redirect(url_for('agent_dashboard'))
        
    return render_template('booking_confirmation.html', booking=booking)

@app.route('/api/flights/update-seat', methods=['POST'])
def api_flights_update_seat():
    data = request.json
    booking_id = data.get('booking_id')
    seat_number = data.get('seat_number')
    
    if not booking_id or not seat_number:
        return jsonify({"success": False, "error": "Missing parameters"}), 400
        
    db = get_db_connection()
    cursor = db.cursor()
    cursor.execute("UPDATE flight_bookings SET seat_number = %s WHERE booking_id = %s", (seat_number, booking_id))
    db.commit()
    
    return jsonify({"success": True})


if __name__ == "__main__":
    app.run(debug=True, host="127.0.0.1", port=5000)



