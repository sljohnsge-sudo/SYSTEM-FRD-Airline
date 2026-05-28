from flask import Flask, render_template, request, redirect, url_for, session, jsonify
import mysql.connector
from decimal import Decimal
import datetime
import random
import os
import socket
socket.setdefaulttimeout(2.0)
from authlib.integrations.flask_client import OAuth
from amadeus import Client, ResponseError

app = Flask(__name__)
app.secret_key = "travel_portal_secret_key_amadeus_b2b"

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
    history_data = None
    error = None
    b2c_user = session.get('b2c_user')
    search_email = session.get('b2c_search_email')
    search_mobile = session.get('b2c_search_mobile')
    
    conn = get_db_connection()
    c = conn.cursor(dictionary=True)
    
    # If user is logged in via Google, fetch their entire history automatically
    if b2c_user:
        try:
            c.execute("""
                SELECT fb.*, b.status as booking_status, b.total_price, b.invoice_number, b.created_at, f.airline, f.flight_number, f.origin, f.destination, f.departure_time, f.arrival_time
                FROM b2c_flight_bookings fb
                JOIN b2c_bookings b ON fb.booking_id = b.id
                JOIN flights f ON fb.flight_id = f.id
                WHERE fb.email = %s
                ORDER BY b.created_at DESC
            """, (b2c_user['email'],))
            history_data = c.fetchall()
        except Exception as e:
            error = f"Could not load booking history: {str(e)}"
    elif search_email and search_mobile:
        try:
            c.execute("""
                SELECT fb.*, b.status as booking_status, b.total_price, b.invoice_number, b.created_at, f.airline, f.flight_number, f.origin, f.destination, f.departure_time, f.arrival_time
                FROM b2c_flight_bookings fb
                JOIN b2c_bookings b ON fb.booking_id = b.id
                JOIN flights f ON fb.flight_id = f.id
                WHERE fb.email = %s AND fb.mobile = %s
                ORDER BY b.created_at DESC
            """, (search_email, search_mobile))
            history_data = c.fetchall()
        except Exception as e:
            error = f"Could not load booking history: {str(e)}"
            
    if request.method == "POST":
        hist_email = request.form.get("hist_email", "").strip()
        hist_mobile = request.form.get("hist_mobile", "").strip()
        
        if not hist_email or not hist_mobile:
            error = "Please provide both Email Address and Mobile Number to view your history."
        else:
            try:
                c.execute("""
                    SELECT fb.*, b.status as booking_status, b.total_price, b.invoice_number, b.created_at, f.airline, f.flight_number, f.origin, f.destination, f.departure_time, f.arrival_time
                    FROM b2c_flight_bookings fb
                    JOIN b2c_bookings b ON fb.booking_id = b.id
                    JOIN flights f ON fb.flight_id = f.id
                    WHERE fb.email = %s AND fb.mobile = %s
                    ORDER BY b.created_at DESC
                """, (hist_email, hist_mobile))
                
                history = c.fetchall()
                if history:
                    history_data = history
                    session['b2c_search_email'] = hist_email
                    session['b2c_search_mobile'] = hist_mobile
                else:
                    error = "No booking history found for this Email and Mobile Number."
                    
            except Exception as e:
                error = f"An error occurred: {str(e)}"
    
    conn.close()
                
    return render_template("b2c_my_bookings.html", booking_data=None, history_data=history_data, error=error)

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

def resolve_iata_code(keyword, amadeus_client=None):
    if not keyword:
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
    # Fallback to Amadeus Location Search API
    if amadeus_client:
        try:
            response = amadeus_client.reference_data.locations.get(
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
    
    # Filter local popular locations first
    matches = []
    seen_codes = set()
    
    for loc in POPULAR_LOCATIONS:
        # Match against city, country, or code
        if not q or q in loc["city"].upper() or q in loc["country"].upper() or q in loc["code"].upper():
            matches.append(loc.copy())
            seen_codes.add(loc["code"])
            
    # Then query Amadeus Reference Data API if we have a query
    if q and len(q) >= 2:
        try:
            amadeus_client = Client(
                client_id='3ZBEyT1bTUzMUPkcEPBUOEKIAkEjgu5o',
                client_secret='2K9Xh5GC2UF9rVo3',
                hostname='test'
            )
            response = amadeus_client.reference_data.locations.get(
                keyword=q,
                subType='AIRPORT,CITY'
            )
            if response.data:
                for item in response.data:
                    code = item.get('iataCode') or item.get('address', {}).get('cityCode')
                    if not code or code in seen_codes:
                        continue
                    
                    address = item.get('address', {})
                    country_name = address.get('countryName', '').upper()
                    country_code = address.get('countryCode', '').upper()
                    city_name = address.get('cityName', '').title() or item.get('name', '').title()
                    airport_name = item.get('name', '').title()
                    
                    if not country_name:
                        continue
                        
                    loc = {
                        "city": city_name,
                        "code": code,
                        "name": f"{airport_name} Arpt" if "Airport" not in airport_name and "Intl" not in airport_name else airport_name,
                        "country": country_name,
                        "country_code": country_code
                    }
                    matches.append(loc)
                    seen_codes.add(code)
        except Exception as e:
            print("Amadeus Reference Data search error:", e)
            
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
        
    # Format as list sorted by country name, prioritizing SRI LANKA
    sorted_groups = []
    countries = sorted(list(grouped.keys()))
    if "SRI LANKA" in countries:
        countries.remove("SRI LANKA")
        countries.insert(0, "SRI LANKA")
        
    for country in countries:
        sorted_groups.append(grouped[country])
        
    return jsonify({"success": True, "groups": sorted_groups})

# API: Search Flights (GDS, LCC, NDC consolidated with round-trip support)
@app.route("/api/flights/search", methods=["GET"])
def api_flights_search():
    origin_input = request.args.get("origin", "").strip()
    destination_input = request.args.get("destination", "").strip()
    flight_type = request.args.get("flight_type", "ALL") # ALL, GDS, LCC, NDC
    date_str = request.args.get("date", "").strip()
    return_date_str = request.args.get("return_date", "").strip()
    airline_filter = request.args.get("airline", "").strip()
    travel_class = request.args.get("travelClass", "ECONOMY").strip()
    
    # Initialize Amadeus client to resolve locations and query flight offers
    amadeus = None
    try:
        amadeus = Client(
            client_id='3ZBEyT1bTUzMUPkcEPBUOEKIAkEjgu5o',
            client_secret='2K9Xh5GC2UF9rVo3',
            hostname='test'
        )
    except Exception as e:
        print("Failed to initialize Amadeus Client:", e)
        
    origin = resolve_iata_code(origin_input, amadeus)
    destination = resolve_iata_code(destination_input, amadeus)
    
    # Fallback to uppercase values if resolution failed to prevent completely empty SQL matching
    if not origin:
        origin = origin_input.upper()
    if not destination:
        destination = destination_input.upper()
    
    amadeus_flight_ids = []
    amadeus_return_flight_ids = []
    
    # Pre-fetch live GDS flights from Amadeus API and cache them in local database
    if flight_type in ["ALL", "GDS"] and origin and destination and date_str:
        try:
            search_params = {
                "originLocationCode": origin,
                "destinationLocationCode": destination,
                "departureDate": date_str,
                "adults": 1,
                "max": 10
            }
            if travel_class != "ALL":
                search_params["travelClass"] = travel_class

            response = amadeus.shopping.flight_offers_search.get(**search_params)
            
            conn = get_db_connection()
            cursor = conn.cursor()
            for f in response.data:
                segments = f['itineraries'][0]['segments']
                flight_no = f"{segments[0]['carrierCode']}-{segments[0]['number']}"
                carrier_code = segments[0]['carrierCode']
                airline = AIRLINE_MAPPING.get(carrier_code, carrier_code)
                # Convert Amadeus EUR to LKR (approx 325 exchange rate)
                price_val = Decimal(str(f['price']['total'])) * Decimal("325.00")
                # Keep first 19 chars for mysql datetime format (YYYY-MM-DD HH:MM:SS)
                dept = segments[0]['departure']['at'].replace('T', ' ')[:19]
                arr = segments[-1]['arrival']['at'].replace('T', ' ')[:19]
                seg_count = len(segments)
                
                # Avoid duplicates and track IDs of fetched flights
                try:
                    cursor.execute("SELECT id FROM flights WHERE flight_number = %s", (flight_no,))
                    row = cursor.fetchone()
                    if row:
                        amadeus_flight_ids.append(row[0])
                        cursor.execute("UPDATE flights SET departure_time = %s, arrival_time = %s, price = %s WHERE id = %s", (dept, arr, price_val, row[0]))
                    else:
                        cursor.execute("""
                            INSERT INTO flights (flight_number, airline, origin, destination, departure_time, arrival_time, price, seats_available, flight_type, segment_count)
                            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, 'GDS', %s)
                        """, (flight_no, airline, origin, destination, dept, arr, price_val, f.get('numberOfBookableSeats', 9), seg_count))
                        amadeus_flight_ids.append(cursor.lastrowid)
                except Exception as ex:
                    print(f"Amadeus API flight loop error for {flight_no}:", ex)
                    
            # Pre-fetch return flights if return date is specified
            if return_date_str:
                try:
                    return_search_params = {
                        "originLocationCode": destination,
                        "destinationLocationCode": origin,
                        "departureDate": return_date_str,
                        "adults": 1,
                        "max": 10
                    }
                    if travel_class != "ALL":
                        return_search_params["travelClass"] = travel_class

                    return_response = amadeus.shopping.flight_offers_search.get(**return_search_params)
                    for f in return_response.data:
                        segments = f['itineraries'][0]['segments']
                        flight_no = f"{segments[0]['carrierCode']}-{segments[0]['number']}"
                        carrier_code = segments[0]['carrierCode']
                        airline = AIRLINE_MAPPING.get(carrier_code, carrier_code)
                        # Convert Amadeus EUR to LKR (approx 325 exchange rate)
                        price_val = Decimal(str(f['price']['total'])) * Decimal("325.00")
                        dept = segments[0]['departure']['at'].replace('T', ' ')[:19]
                        arr = segments[-1]['arrival']['at'].replace('T', ' ')[:19]
                        seg_count = len(segments)
                        
                        try:
                            cursor.execute("SELECT id FROM flights WHERE flight_number = %s", (flight_no,))
                            row = cursor.fetchone()
                            if row:
                                amadeus_return_flight_ids.append(row[0])
                                cursor.execute("UPDATE flights SET departure_time = %s, arrival_time = %s, price = %s WHERE id = %s", (dept, arr, price_val, row[0]))
                            else:
                                cursor.execute("""
                                    INSERT INTO flights (flight_number, airline, origin, destination, departure_time, arrival_time, price, seats_available, flight_type, segment_count)
                                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, 'GDS', %s)
                                """, (flight_no, airline, destination, origin, dept, arr, price_val, f.get('numberOfBookableSeats', 9), seg_count))
                                amadeus_return_flight_ids.append(cursor.lastrowid)
                        except Exception as ex:
                            print(f"Amadeus Return API flight loop error for {flight_no}:", ex)
                except Exception as ex:
                    print("Amadeus Return API error:", ex)
                    
            conn.commit()
            cursor.close()
            conn.close()
        except Exception as e:
            print("Amadeus API error:", e)
 
    # Query outbound flights
    if origin and destination and date_str:
        if amadeus_flight_ids:
            format_strings = ','.join(['%s'] * len(amadeus_flight_ids))
            query = f"SELECT * FROM flights WHERE id IN ({format_strings}) ORDER BY price ASC"
            params = amadeus_flight_ids
            flights = query_db(query, tuple(params))
        else:
            # Fallback to local DB without strict date match to ensure mock data shows up
            query = "SELECT * FROM flights WHERE origin = %s AND destination = %s"
            params = [origin, destination]
            if flight_type != "ALL":
                query += " AND flight_type = %s"
                params.append(flight_type)
            if airline_filter:
                query += " AND airline LIKE %s"
                params.append(f"%{airline_filter}%")
            query += " ORDER BY price ASC"
            flights = query_db(query, tuple(params))
            
            # If still no flights, generate mock fallback data for this route
            if not flights and date_str:
                conn = get_db_connection()
                cursor = conn.cursor()
                airlines = ['UL', 'EK', 'QR', 'SQ', 'CX', 'MH', 'TG']
                for _ in range(15):
                    al = random.choice(airlines)
                    fno = f"{al}-{random.randint(100, 9999)}"
                    price_val = round(random.uniform(45000, 180000), 2)
                    seats = random.randint(2, 9)
                    req_date = datetime.datetime.strptime(date_str, "%Y-%m-%d").date()
                    dept_time = datetime.datetime.combine(req_date, datetime.time(random.randint(0,23), random.choice([0,15,30,45])))
                    arr_time = dept_time + datetime.timedelta(hours=random.randint(1, 14), minutes=random.choice([0,15,30,45]))
                    
                    cursor.execute("""
                        INSERT INTO flights (flight_number, airline, origin, destination, departure_time, arrival_time, price, seats_available, flight_type, segment_count)
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, 'GDS', %s)
                    """, (fno, AIRLINE_MAPPING.get(al, al), origin, destination, dept_time, arr_time, price_val, seats, random.randint(1,3)))
                conn.commit()
                cursor.close()
                conn.close()
                flights = query_db(query, tuple(params))
            
            # Adjust the departure date of the mock flights to match the requested date
            if date_str:
                requested_date = datetime.datetime.strptime(date_str, "%Y-%m-%d").date()
                for f in flights:
                    orig_dep = f["departure_time"]
                    orig_arr = f["arrival_time"]
                    time_diff = orig_arr - orig_dep
                    new_dep = datetime.datetime.combine(requested_date, orig_dep.time())
                    new_arr = new_dep + time_diff
                    f["departure_time"] = new_dep
                    f["arrival_time"] = new_arr
    else:
        # Fallback for initial load or general listing to keep other non-search components operational
        query = "SELECT * FROM flights WHERE 1=1"
        params = []
        if origin:
            query += " AND origin = %s"
            params.append(origin)
        if destination:
            query += " AND destination = %s"
            params.append(destination)
        if date_str:
            query += " AND DATE(departure_time) = %s"
            params.append(date_str)
        if flight_type != "ALL":
            query += " AND flight_type = %s"
            params.append(flight_type)
        if airline_filter:
            query += " AND airline LIKE %s"
            params.append(f"%{airline_filter}%")
        query += " ORDER BY price ASC"
        flights = query_db(query, tuple(params))
        
    # Query return flights if return date is specified
    return_flights = []
    if return_date_str and origin and destination:
        if amadeus_return_flight_ids:
            format_strings = ','.join(['%s'] * len(amadeus_return_flight_ids))
            query = f"SELECT * FROM flights WHERE id IN ({format_strings}) ORDER BY price ASC"
            params = amadeus_return_flight_ids
            return_flights = query_db(query, tuple(params))
        else:
            query = "SELECT * FROM flights WHERE origin = %s AND destination = %s"
            params = [destination, origin]
            if flight_type != "ALL":
                query += " AND flight_type = %s"
                params.append(flight_type)
            if airline_filter:
                query += " AND airline LIKE %s"
                params.append(f"%{airline_filter}%")
            query += " ORDER BY price ASC"
            return_flights = query_db(query, tuple(params))
            
            # Adjust the departure date of the mock flights to match the requested date
            if return_date_str:
                requested_ret_date = datetime.datetime.strptime(return_date_str, "%Y-%m-%d").date()
                for f in return_flights:
                    orig_dep = f["departure_time"]
                    orig_arr = f["arrival_time"]
                    time_diff = orig_arr - orig_dep
                    new_dep = datetime.datetime.combine(requested_ret_date, orig_dep.time())
                    new_arr = new_dep + time_diff
                    f["departure_time"] = new_dep
                    f["arrival_time"] = new_arr
            
        # Fallback clone return flights if no return flights found but outbound flights exist
        if not return_flights and flights:
            conn = get_db_connection()
            cursor = conn.cursor(dictionary=True)
            for f in flights:
                ret_flight_no = f"RET-{f['flight_number']}"
                dept_dt = datetime.datetime.strptime(return_date_str, "%Y-%m-%d") + datetime.timedelta(hours=14)
                arr_dt = dept_dt + datetime.timedelta(hours=3)
                
                cursor.execute("SELECT * FROM flights WHERE flight_number = %s AND origin = %s", (ret_flight_no, destination))
                existing = cursor.fetchone()
                if existing:
                    return_flights.append(existing)
                else:
                    cursor.execute("""
                        INSERT INTO flights (flight_number, airline, origin, destination, departure_time, arrival_time, price, seats_available, flight_type, segment_count)
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    """, (ret_flight_no, f["airline"], destination, origin, dept_dt, arr_dt, Decimal(str(f["price"])), f["seats_available"], f["flight_type"], f["segment_count"]))
                    
                    new_id = cursor.lastrowid
                    cursor.execute("SELECT * FROM flights WHERE id = %s", (new_id,))
                    new_f = cursor.fetchone()
                    return_flights.append(new_f)
            conn.commit()
            cursor.close()
            conn.close()
            
    # Serialize helper
    def serialize_flight(f):
        f_copy = f.copy()
        if isinstance(f_copy["price"], Decimal):
            f_copy["price"] = float(f_copy["price"])
        # Normalize price to LKR: if price is < 10000 it is stored in USD (seeded flights),
        # multiply by 300 to convert to approximate LKR. Mock flights are already in LKR (45000+).
        if f_copy["price"] < 10000:
            f_copy["price"] = round(f_copy["price"] * 300, 2)
        if isinstance(f_copy["departure_time"], (datetime.datetime, datetime.date)):
            f_copy["departure_time"] = f_copy["departure_time"].isoformat()
        if isinstance(f_copy["arrival_time"], (datetime.datetime, datetime.date)):
            f_copy["arrival_time"] = f_copy["arrival_time"].isoformat()
        return f_copy
        
    # Pair flights if return_date is specified
    if return_date_str and return_flights:
        paired_flights = []
        for out_f in flights:
            matching_ret = None
            for ret_f in return_flights:
                if ret_f["airline"] == out_f["airline"]:
                    matching_ret = ret_f
                    break
            if not matching_ret:
                matching_ret = return_flights[0]
                
            out_serialized = serialize_flight(out_f)
            ret_serialized = serialize_flight(matching_ret)
            
            # Combine pricing and structure
            out_serialized["return_flight"] = ret_serialized
            out_serialized["price"] = out_serialized["price"] + ret_serialized["price"]
            paired_flights.append(out_serialized)
        flights = paired_flights
    else:
        flights = [serialize_flight(f) for f in flights]
        
    return jsonify({"success": True, "flights": flights})
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
        
    data = request.json
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
    ticket_now = data.get("ticket_now", False) # True = Ticketed, False = Non-Ticketed reservation
    
    return_flight_id = data.get("return_flight_id")
    return_seat_number = data.get("return_seat_number", "14F")
    
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
            
        if not bypass_seat_selection and flight["seats_available"] <= 0:
            return jsonify({"success": False, "error": "No seats available on this flight"}), 400
            
        return_flight = None
        if return_flight_id:
            cursor.execute("SELECT * FROM flights WHERE id = %s", (return_flight_id,))
            return_flight = cursor.fetchone()
            if not return_flight:
                return jsonify({"success": False, "error": "Return flight not found"}), 404
            if not bypass_seat_selection and return_flight["seats_available"] <= 0:
                return jsonify({"success": False, "error": "No seats available on return flight"}), 400
            
        # Get issuance markup
        cursor.execute("SELECT amount FROM service_fees WHERE transaction_type = 'issuance'")
        fee = cursor.fetchone()
        markup = Decimal(str(fee["amount"])) if fee else Decimal("15.00")
        
        # Determine passenger count from request payload or by parsing names joined by ' & '
        if passengers:
            pax_count = len(passengers)
        else:
            pax_count = 1
            passenger_names = [n.strip() for n in passenger_name.split('&') if n.strip()]
            if passenger_names:
                pax_count = max(int(data.get("passenger_count", len(passenger_names))), len(passenger_names))
            else:
                pax_count = int(data.get("passenger_count", 1))
        pax_count = max(1, pax_count)
        
        # Normalize prices to LKR: seeded flights are stored in USD (< 10000), mock flights are already in LKR
        LKR_RATE = Decimal("300")
        flight_price_lkr = flight["price"] if flight["price"] >= Decimal("10000") else flight["price"] * LKR_RATE
        
        if return_flight:
            ret_price_lkr = return_flight["price"] if return_flight["price"] >= Decimal("10000") else return_flight["price"] * LKR_RATE
            orig_price = (flight_price_lkr + ret_price_lkr) * Decimal(str(pax_count))
            total_price = orig_price + (2 * markup * Decimal(str(pax_count)))
        else:
            orig_price = flight_price_lkr * Decimal(str(pax_count))
            total_price = orig_price + (markup * Decimal(str(pax_count)))
            
        extra_seat_charge = Decimal(str(data.get("extra_seat_charge", 0)))
        total_price += extra_seat_charge
        
        # Check credit balance for B2B only
        agent_credit = Decimal("0.00")
        if not is_b2c:
            cursor.execute("SELECT credit_balance FROM users WHERE id = %s", (session["user_id"],))
            agent_credit = cursor.fetchone()["credit_balance"]
        
        booking_status = "ticketed" if ticket_now else "non-ticketed"
        
        # Calculate the actual payment amount to deduct/charge
        payment_method = data.get("payment_method", "credit")
        active_booking_path = data.get("active_booking_path", "ticket")
        
        if active_booking_path == "hold":
            payment_to_charge = Decimal("2.00")
        else:
            payment_to_charge = total_price
            
        full_ticket_value = total_price
            
        if is_b2c and "modifying_booking_id" in session:
            old_price = Decimal(str(session.get("modifying_old_price", 0)))
            payment_to_charge = payment_to_charge - old_price
            if payment_to_charge < 0:
                payment_to_charge = Decimal("0.00")
            
        if not is_b2c and payment_method == "credit" and agent_credit < payment_to_charge:
            return jsonify({
                "success": False, 
                "error": "Insufficient credit balance to process this payment. Please top up your account.",
                "code": "INSUFFICIENT_CREDIT"
            }), 400
            
        # Generate Invoice and Booking
        invoice_number = f"INV-F{random.randint(100000, 999999)}"
        
        # If passengers list not present, fallback to legacy single passenger structure
        if not passengers:
            passengers = [{
                "title": "",
                "first_name": passenger_name,
                "last_name": "",
                "passport_number": passport_number,
                "mobile": mobile,
                "email": email,
                "meal_preference": data.get("meal_preference", "Standard Meal"),
                "wheelchair_assistance": data.get("wheelchair_assistance", "No wheelchair assistance required"),
                "airport_assistance": data.get("airport_assistance", "No special airport assistance"),
                "allergy_conditions": data.get("allergy_conditions", ""),
                "other_requests": data.get("other_requests", "")
            }]
            
        # Prepare seat lists
        seat_list = [s.strip() for s in seat_number.split(',') if s.strip()]
        return_seat_list = [s.strip() for s in return_seat_number.split(',') if s.strip()] if return_flight_id else []

        pnr_reference = f"PNR{random.randint(100000, 999999)}"
        return_pnr = f"PNR{random.randint(100000, 999999)}" if return_flight_id else None
        ticket_number = None
        ticket_numbers = []
        
        if is_b2c:
            cursor.execute("""
                INSERT INTO b2c_bookings (b2c_user_id, booking_type, status, total_price, invoice_number, created_at)
                VALUES (NULL, 'flight', %s, %s, %s, NOW())
            """, (booking_status, full_ticket_value, invoice_number))
            booking_id = cursor.lastrowid
            
            outbound_gds_type = (flight.get("gds_source") or "Amadeus") if flight.get("flight_type") == "GDS" else flight.get("flight_type")
            return_gds_type = None
            if return_flight:
                return_gds_type = (return_flight.get("gds_source") or "Amadeus") if return_flight.get("flight_type") == "GDS" else return_flight.get("flight_type")
            
            for idx, p in enumerate(passengers):
                p_title = p.get("title", "")
                p_first = p.get("first_name", "")
                p_last = p.get("last_name", "")
                p_name = f"{p_title} {p_first} {p_last}".strip() if (p_title or p_last) else p_first
                if not p_name:
                    p_name = passenger_name
                
                p_passport = p.get("passport_number") or passport_number
                p_mobile = p.get("mobile") or mobile
                p_email = p.get("email") or email
                p_meal = p.get("meal_preference", "Standard Meal")
                p_wc = p.get("wheelchair_assistance", "No wheelchair assistance required")
                p_ap = p.get("airport_assistance", "No special airport assistance")
                p_al = p.get("allergy_conditions", "")
                p_o = p.get("other_requests", "")
                
                p_seat = seat_list[idx] if idx < len(seat_list) else (seat_number or "14A")
                p_ticket = f"TKT-{random.randint(1000000000, 9999999999)}" if booking_status == "ticketed" else None
                if p_ticket:
                    ticket_numbers.append(p_ticket)
                if idx == 0:
                    ticket_number = p_ticket

                cursor.execute("""
                    INSERT INTO b2c_flight_bookings (booking_id, flight_id, passenger_name, seat_number, gds_type, ticket_status, original_price, service_fee, pnr_reference, ticket_number, passport_number, mobile, email, meal_preference, wheelchair_assistance, airport_assistance, allergy_conditions, other_requests)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                """, (booking_id, flight_id, p_name, p_seat, outbound_gds_type, booking_status, flight["price"], markup, pnr_reference, p_ticket, p_passport, p_mobile, p_email, p_meal, p_wc, p_ap, p_al, p_o))
                
                if return_flight:
                    return_ticket = f"TKT-{random.randint(1000000000, 9999999999)}" if booking_status == "ticketed" else None
                    p_return_seat = return_seat_list[idx] if idx < len(return_seat_list) else (return_seat_number or "14F")
                    
                    cursor.execute("""
                        INSERT INTO b2c_flight_bookings (booking_id, flight_id, passenger_name, seat_number, gds_type, ticket_status, original_price, service_fee, pnr_reference, ticket_number, passport_number, mobile, email, meal_preference, wheelchair_assistance, airport_assistance, allergy_conditions, other_requests)
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    """, (booking_id, return_flight_id, p_name, p_return_seat, return_gds_type, booking_status, return_flight["price"], markup, return_pnr, return_ticket, p_passport, p_mobile, p_email, p_meal, p_wc, p_ap, p_al, p_o))
            
            if "modifying_booking_id" in session:
                cursor.execute("UPDATE b2c_bookings SET status = 'Cancelled' WHERE id = %s", (session["modifying_booking_id"],))
                session.pop("modifying_booking_id", None)
                session.pop("modifying_old_price", None)
        
        else:
            agent_id = session["user_id"]
            cursor.execute("""
                INSERT INTO bookings (agent_id, booking_type, status, total_price, invoice_number, created_at)
                VALUES (%s, 'flight', %s, %s, %s, NOW())
            """, (agent_id, booking_status, payment_to_charge, invoice_number))
            
            booking_id = cursor.lastrowid
            
            outbound_gds_type = (flight.get("gds_source") or "Amadeus") if flight.get("flight_type") == "GDS" else flight.get("flight_type")
            return_gds_type = None
            if return_flight:
                return_gds_type = (return_flight.get("gds_source") or "Amadeus") if return_flight.get("flight_type") == "GDS" else return_flight.get("flight_type")
            
            for idx, p in enumerate(passengers):
                p_title = p.get("title", "")
                p_first = p.get("first_name", "")
                p_last = p.get("last_name", "")
                p_name = f"{p_title} {p_first} {p_last}".strip() if (p_title or p_last) else p_first
                if not p_name:
                    p_name = passenger_name
                
                p_passport = p.get("passport_number") or passport_number
                p_mobile = p.get("mobile") or mobile
                p_email = p.get("email") or email
                p_meal = p.get("meal_preference", "Standard Meal")
                p_wc = p.get("wheelchair_assistance", "No wheelchair assistance required")
                p_ap = p.get("airport_assistance", "No special airport assistance")
                p_al = p.get("allergy_conditions", "")
                p_o = p.get("other_requests", "")
                
                p_seat = seat_list[idx] if idx < len(seat_list) else (seat_number or "14A")
                p_ticket = f"TKT-{random.randint(1000000000, 9999999999)}" if booking_status == "ticketed" else None
                if p_ticket:
                    ticket_numbers.append(p_ticket)
                if idx == 0:
                    ticket_number = p_ticket

                cursor.execute("""
                    INSERT INTO flight_bookings (booking_id, flight_id, passenger_name, seat_number, gds_type, ticket_status, original_price, service_fee, pnr_reference, ticket_number, passport_number, mobile, email, meal_preference, wheelchair_assistance, airport_assistance, allergy_conditions, other_requests)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                """, (booking_id, flight_id, p_name, p_seat, outbound_gds_type, booking_status, flight["price"], markup, pnr_reference, p_ticket, p_passport, p_mobile, p_email, p_meal, p_wc, p_ap, p_al, p_o))
                
                if return_flight:
                    return_ticket = f"TKT-{random.randint(1000000000, 9999999999)}" if booking_status == "ticketed" else None
                    p_return_seat = return_seat_list[idx] if idx < len(return_seat_list) else (return_seat_number or "14F")
                    
                    cursor.execute("""
                        INSERT INTO flight_bookings (booking_id, flight_id, passenger_name, seat_number, gds_type, ticket_status, original_price, service_fee, pnr_reference, ticket_number, passport_number, mobile, email, meal_preference, wheelchair_assistance, airport_assistance, allergy_conditions, other_requests)
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    """, (booking_id, return_flight_id, p_name, p_return_seat, return_gds_type, booking_status, return_flight["price"], markup, return_pnr, return_ticket, p_passport, p_mobile, p_email, p_meal, p_wc, p_ap, p_al, p_o))
            
        # Deduct wallet if credit option is used (only valid for B2B)
        if payment_method == "credit" and not is_b2c:
            cursor.execute("UPDATE users SET credit_balance = credit_balance - %s WHERE id = %s", (payment_to_charge, session["user_id"]))
            
        # If ticketed immediately, deduct seat count and award loyalty points
        if booking_status == "ticketed":
            # Deduct seat count for outbound
            cursor.execute("UPDATE flights SET seats_available = seats_available - %s WHERE id = %s", (pax_count, flight_id))
            # Deduct seat count for return
            if return_flight:
                cursor.execute("UPDATE flights SET seats_available = seats_available - %s WHERE id = %s", (pax_count, return_flight_id))
                
            # Award loyalty rewards for B2B
            if not is_b2c:
                reward_points = int(payment_to_charge / 10)
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
            "booking_id": booking_id,
            "pnr_reference": pnr_reference,
            "ticket_number": ticket_number,
            "ticket_numbers": ticket_numbers
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
    
    # Call Amadeus API if location is provided
    if location:
        try:
            amadeus = Client(
                client_id='3ZBEyT1bTUzMUPkcEPBUOEKIAkEjgu5o',
                client_secret='2K9Xh5GC2UF9rVo3',
                hostname='test'
            )
            
            # Resolve City Code if not a 3-letter code
            city_code = None
            if len(location) == 3 and location.isalpha():
                city_code = location.upper()
            else:
                loc_response = amadeus.reference_data.locations.get(
                    keyword=location,
                    subType='CITY'
                )
                if loc_response.data:
                    city_code = loc_response.data[0]['address']['cityCode']
                    
            if city_code:
                # Get hotels in that city
                hotels_response = amadeus.reference_data.locations.hotels.by_city.get(
                    cityCode=city_code
                )
                
                if hotels_response.data:
                    conn = get_db_connection()
                    cursor = conn.cursor(dictionary=True)
                    # Limit to top 5 hotels to avoid performance issues
                    for h_data in hotels_response.data[:5]:
                        hotel_name = h_data['name'].title()
                        hotel_loc = f"{h_data['address'].get('cityName', city_code).title()}, {h_data['address'].get('countryCode', '')}"
                        
                        # Check if hotel already exists
                        cursor.execute("SELECT id FROM hotels WHERE name = %s", (hotel_name,))
                        existing = cursor.fetchone()
                        
                        if not existing:
                            # Insert hotel
                            desc = f"A premium hotel in {hotel_loc} sourced via Amadeus GDS. Offers comfortable lodging and premium amenities."
                            # Random rating from 3 to 5
                            rating = random.randint(3, 5)
                            # Pick a random placeholder image or generic name
                            img_url = f"hotel_{city_code.lower()}_{random.randint(1,3)}.jpg"
                            
                            cursor.execute("""
                                INSERT INTO hotels (name, location, rating, description, image_url)
                                VALUES (%s, %s, %s, %s, %s)
                            """, (hotel_name, hotel_loc, rating, desc, img_url))
                            hotel_id = cursor.lastrowid
                            
                            # Insert rooms for this hotel
                            rooms_data = [
                                ('Standard Single Room', Decimal(str(random.randint(80, 150)))),
                                ('Deluxe Double Room', Decimal(str(random.randint(180, 300)))),
                                ('Executive Luxury Suite', Decimal(str(random.randint(400, 750))))
                            ]
                            for room_type, price in rooms_data:
                                cursor.execute("""
                                    INSERT INTO rooms (hotel_id, room_type, price_per_night, availability)
                                    VALUES (%s, %s, %s, 1)
                                """, (hotel_id, room_type, price))
                    conn.commit()
                    cursor.close()
                    conn.close()
        except Exception as e:
            print("Amadeus Hotel API error:", e)

    query = "SELECT * FROM hotels WHERE 1=1"
    params = []
    
    if location:
        query += " AND (location LIKE %s OR name LIKE %s)"
        params.append(f"%{location}%")
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
            segments = query_db("""
                SELECT flight_bookings.*, flights.flight_number, flights.airline, flights.origin, flights.destination, flights.departure_time 
                FROM flight_bookings 
                JOIN flights ON flight_bookings.flight_id = flights.id 
                WHERE flight_bookings.booking_id = %s
                ORDER BY flight_bookings.id ASC
            """, (b["id"],))
            if segments:
                details = segments[0]
                details["original_price"] = float(details["original_price"])
                details["service_fee"] = float(details["service_fee"])
                details["departure_time"] = details["departure_time"].isoformat()
                
                # Check for return segment (second row)
                if len(segments) > 1:
                    ret_details = segments[1]
                    ret_details["original_price"] = float(ret_details["original_price"])
                    ret_details["service_fee"] = float(ret_details["service_fee"])
                    ret_details["departure_time"] = ret_details["departure_time"].isoformat()
                    details["return_segment"] = ret_details
                    
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
        
        # Deduct credit
        cursor.execute("UPDATE users SET credit_balance = credit_balance - %s WHERE id = %s", (total_price, session["user_id"]))
        
        # Select and ticket all segments
        cursor.execute("SELECT id, flight_id FROM flight_bookings WHERE booking_id = %s", (booking_id,))
        segments = cursor.fetchall()
        for seg in segments:
            tkt_num = f"TKT-{random.randint(1000000000, 9999999999)}"
            cursor.execute("UPDATE flight_bookings SET ticket_status = 'ticketed', ticket_number = %s WHERE id = %s", (tkt_num, seg["id"]))
            cursor.execute("UPDATE flights SET seats_available = seats_available - 1 WHERE id = %s", (seg["flight_id"],))
        
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
        <div style='background: white; border: 1px solid #cbd5e1; border-radius: 12px; padding: 15px; margin-top: 10px; color: #1e293b; text-align: left; box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);'>
            <div style='font-weight: 800; color: #1e3a8a; font-size: 15px; margin-bottom: 8px;'><i class='fa-solid fa-plane-departure'></i> Best Flight Found</div>
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
            <a href='/b2c-flight-results?origin={origin}&dest={dest}&date={date}&adults=1' style='display: block; text-align: center; background: #d11242; color: white; padding: 10px; border-radius: 8px; text-decoration: none; font-size: 14px; font-weight: bold; transition: background 0.3s;'>Book This Flight Now</a>
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

if __name__ == "__main__":
    app.run(debug=True, host="127.0.0.1", port=5000)
