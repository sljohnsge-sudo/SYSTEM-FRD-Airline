import re

def rewrite_api_bookings_ticket():
    with open(r'd:\GS\SYSTEM-FRD-Airline\app.py', 'r', encoding='utf-8') as f:
        content = f.read()
        
    pattern = re.compile(r'(@app\.route\("/api/bookings/ticket", methods=\["POST"\]\)\ndef api_bookings_ticket\(\):.*?)(?=@app\.route\("/api/bookings/reissue", methods=\["POST"\]\))', re.DOTALL)
    
    replacement = """@app.route("/api/bookings/ticket", methods=["POST"])
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
            
            tkt_num = tp_res.get("ticket_number", f"TKT-{pnr}")
            
            cursor.execute("UPDATE flight_bookings SET ticket_status = 'ticketed', ticket_number = %s WHERE id = %s", (tkt_num, seg["id"]))
            cursor.execute("UPDATE flights SET seats_available = seats_available - 1 WHERE id = %s", (seg["flight_id"],))
            
        # Update status
        cursor.execute("UPDATE bookings SET status = 'ticketed' WHERE id = %s", (booking_id,))
        
        # Deduct credit
        cursor.execute("UPDATE users SET credit_balance = credit_balance - %s WHERE id = %s", (total_price, session["user_id"]))
        
        # Award loyalty points
        reward_points = int(total_price / 10)
        cursor.execute(\"\"\"
            INSERT INTO agent_rewards (agent_id, reward_points, description)
            VALUES (%s, %s, %s)
        \"\"\", (session["user_id"], reward_points, f"Points earned for ticket issuance {booking['invoice_number']}"))
        
        conn.commit()
        return jsonify({"success": True, "message": "Reservation ticketed successfully via Travelport API! Balance updated."})
        
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
        
    print("Replaced api_bookings_ticket!")

if __name__ == "__main__":
    rewrite_api_bookings_ticket()
