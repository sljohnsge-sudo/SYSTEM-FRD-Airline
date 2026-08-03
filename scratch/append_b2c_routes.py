with open(r'd:\GS\SYSTEM-FRD-Airline\app.py', 'a', encoding='utf-8') as f:
    f.write("""

# ==========================================
# B2C ADMIN PORTAL APIS
# ==========================================

@app.route("/api/admin/b2c/users")
def api_admin_b2c_users():
    if "user_id" not in session or session.get("role") != "admin":
        return jsonify({"success": False, "error": "Unauthorized"}), 401
    users = query_db("SELECT id, username, email, phone, registered_at FROM b2c_users ORDER BY registered_at DESC")
    for u in users:
        u["registered_at"] = u["registered_at"].isoformat() if u["registered_at"] else ""
    return jsonify({"success": True, "users": users})

@app.route("/api/admin/b2c/fees/list")
def api_admin_b2c_fees_list():
    if "user_id" not in session or session.get("role") != "admin":
        return jsonify({"success": False, "error": "Unauthorized"}), 401
    fees = query_db("SELECT * FROM b2c_service_fees")
    for f in fees:
        f["amount"] = float(f["amount"])
    return jsonify({"success": True, "fees": fees})

@app.route("/api/admin/b2c/fees/update", methods=["POST"])
def api_admin_b2c_fees_update():
    if "user_id" not in session or session.get("role") != "admin":
        return jsonify({"success": False, "error": "Unauthorized"}), 401
    data = request.json
    fee_id = data.get("id")
    amount = data.get("amount")
    amount_type = data.get("amount_type")
    if not fee_id or amount is None or amount_type not in ["fixed", "percentage"]:
        return jsonify({"success": False, "error": "Invalid parameters"}), 400
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("UPDATE b2c_service_fees SET amount = %s, amount_type = %s WHERE id = %s", (amount, amount_type, fee_id))
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
    if "user_id" not in session or session.get("role") != "admin":
        return jsonify({"success": False, "error": "Unauthorized"}), 401
    bookings = query_db("SELECT id, b2c_user_id, pnr, total_price, status, created_at FROM b2c_flight_bookings ORDER BY created_at DESC LIMIT 50")
    for b in bookings:
        b["total_price"] = float(b["total_price"])
        b["created_at"] = b["created_at"].isoformat() if b["created_at"] else ""
    return jsonify({"success": True, "bookings": bookings})
""")
