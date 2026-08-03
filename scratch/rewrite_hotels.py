import re

def rewrite_api_hotels_search():
    with open(r'd:\GS\SYSTEM-FRD-Airline\app.py', 'r', encoding='utf-8') as f:
        content = f.read()
        
    pattern = re.compile(r'(@app\.route\("/api/hotels/search", methods=\["GET"\]\)\ndef api_hotels_search\(\):.*?)(?=@app\.route\("/api/pnr/retrieve", methods=\["GET"\]\))', re.DOTALL)
    
    replacement = """@app.route("/api/hotels/search", methods=["GET"])
def api_hotels_search():
    location = request.args.get("location", "").strip()
    
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    
    try:
        # Since Travelport Hotel API documentation wasn't provided, 
        # and we are strictly not allowed to use dummy APIs, we only return 
        # what currently exists in the authentic hotels database.
        
        query = "SELECT * FROM hotels"
        params = []
        
        if location:
            query += " WHERE location LIKE %s OR name LIKE %s"
            params.extend([f"%{location}%", f"%{location}%"])
            
        query += " ORDER BY price_per_night ASC"
        
        cursor.execute(query, tuple(params))
        hotels = cursor.fetchall()
        
        return jsonify({"success": True, "hotels": hotels})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500
    finally:
        cursor.close()
        conn.close()

"""
    
    new_content = pattern.sub(replacement, content)
    
    with open(r'd:\GS\SYSTEM-FRD-Airline\app.py', 'w', encoding='utf-8') as f:
        f.write(new_content)
        
    print("Replaced api_hotels_search!")

if __name__ == "__main__":
    rewrite_api_hotels_search()
