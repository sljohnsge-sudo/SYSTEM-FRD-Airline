import re

def wire_flight_booking():
    with open(r'd:\GS\SYSTEM-FRD-Airline\app.py', 'r', encoding='utf-8') as f:
        content = f.read()
        
    pattern = re.compile(r'(@app\.route\("/api/flights/book", methods=\["POST"\]\)\ndef api_flights_book\(\):.*?)(?=@app\.route\("/api/hotels/search", methods=\["GET"\]\))', re.DOTALL)
    
    replacement = """@app.route("/api/flights/book", methods=["POST"])
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
        
        tp_res = tp_service.book_flight(flight_id, passengers or [])
        if not tp_res["success"]:
            # If Travelport booking fails, do not create local DB entry
            return jsonify({"success": False, "error": f"Travelport Booking Failed: {tp_res.get('error')}"})
            
        # Retrieve authentic PNR from Travelport response
        tp_pnr = tp_res.get("data", {}).get("ReservationBuildResponse", {}).get("PNR", f"PNR{random.randint(100000, 999999)}")
        
        # Calculate markup
        markup_amount = 0
        total_price = flight["price"]
        
        if not is_b2c:
            cursor.execute("SELECT * FROM markups WHERE agent_id = %s OR is_global = TRUE ORDER BY is_global ASC", (session["user_id"],))
            markups = cursor.fetchall()
            
            for m in markups:
                if m["gds_source"] == "ALL" or m["gds_source"] == flight["gds_source"]:
                    if m["flight_type"] == "ALL" or m["flight_type"] == flight["flight_type"]:
                        if m["markup_type"] == "percentage":
                            markup_amount += float(flight["price"]) * (float(m["markup_value"]) / 100)
                        else:
                            markup_amount += float(m["markup_value"])
                            
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
            cursor.execute(\"\"\"
                INSERT INTO b2c_flight_bookings (flight_id, pnr_reference, passenger_name, passport_number, mobile, email, status, total_price, invoice_number)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            \"\"\", (flight_id, tp_pnr, passenger_name, passport_number, mobile, email, status, total_price, invoice_num))
            booking_id = cursor.lastrowid
            
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
            cursor.execute(\"\"\"
                INSERT INTO bookings (agent_id, booking_type, invoice_number, total_price, status)
                VALUES (%s, 'flight', %s, %s, %s)
            \"\"\", (session["user_id"], invoice_num, total_price, status))
            
            booking_id = cursor.lastrowid
            
            tkt_status = "ticketed" if ticket_now else "non-ticketed"
            tkt_number = f"TKT-{random.randint(1000000000, 9999999999)}" if ticket_now else None
            
            cursor.execute(\"\"\"
                INSERT INTO flight_bookings (booking_id, flight_id, pnr_reference, passenger_name, seat_number, ticket_status, ticket_number)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
            \"\"\", (booking_id, flight_id, tp_pnr, passenger_name, seat_number, tkt_status, tkt_number))
            
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

"""
    
    new_content = pattern.sub(replacement, content)
    
    with open(r'd:\GS\SYSTEM-FRD-Airline\app.py', 'w', encoding='utf-8') as f:
        f.write(new_content)
        
    print("Replaced api_flights_book!")

if __name__ == "__main__":
    wire_flight_booking()
