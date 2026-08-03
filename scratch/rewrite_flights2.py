import re

def rewrite_api_flights_search_with_db():
    with open(r'd:\GS\SYSTEM-FRD-Airline\app.py', 'r', encoding='utf-8') as f:
        content = f.read()
        
    pattern = re.compile(r'(@app\.route\("/api/flights/search", methods=\["GET"\]\)\ndef api_flights_search\(\):.*?)(?=@app\.route\("/api/flights/seat-availability", methods=\["POST"\]\))', re.DOTALL)
    
    replacement = """@app.route("/api/flights/search", methods=["GET"])
def api_flights_search():
    from services.travelport_service import TravelportService
    
    origin = request.args.get("origin", "").strip().upper()
    destination = request.args.get("destination", "").strip().upper()
    date_str = request.args.get("date", "").strip()
    adults = request.args.get("adults", "1").strip()
    
    tp_service = TravelportService()
    response = tp_service.search_flights(origin, destination, date_str, adults=adults)
    
    if not response["success"]:
        return jsonify({"success": False, "error": response.get("error", "Failed to search flights on Travelport API.")})
        
    tp_data = response["data"]
    formatted_flights = []
    offerings = tp_data.get("CatalogOfferings", {}).get("CatalogOffering", [])
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    for idx, offering in enumerate(offerings):
        try:
            product_info = offering.get("Product", [{}])[0]
            flights_segments = product_info.get("FlightSegment", [])
            
            segments = []
            for seg in flights_segments:
                segments.append({
                    "carrierCode": seg.get("carrier"),
                    "number": seg.get("flightNumber"),
                    "departure": {
                        "at": seg.get("departure", {}).get("time")
                    },
                    "arrival": {
                        "at": seg.get("arrival", {}).get("time")
                    }
                })
            
            total_price_str = offering.get("Price", {}).get("TotalPrice", {}).get("Total", "0.0")
            try:
                price_val = float(total_price_str)
                price_lkr = price_val * 325.0
            except ValueError:
                price_lkr = 0.0
                
            airline = segments[0]["carrierCode"] if segments else "Unknown"
            flight_number = f"{segments[0]['carrierCode']}-{segments[0]['number']}" if segments else "Unknown"
            dept_time = segments[0]["departure"]["at"].replace('T', ' ')[:19] if segments else ""
            arr_time = segments[-1]["arrival"]["at"].replace('T', ' ')[:19] if segments else ""
            seats_avail = offering.get("numberOfBookableSeats", 9)
            segment_count = len(segments)
            
            # Save to DB so it can be booked
            cursor.execute("SELECT id FROM flights WHERE flight_number = %s AND departure_time = %s", (flight_number, dept_time))
            row = cursor.fetchone()
            if row:
                flight_id = row[0]
            else:
                cursor.execute(\"\"\"
                    INSERT INTO flights (flight_number, airline, origin, destination, departure_time, arrival_time, price, seats_available, flight_type, segment_count)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, 'GDS', %s)
                \"\"\", (flight_number, airline, origin, destination, dept_time, arr_time, price_lkr, seats_avail, segment_count))
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
        "outbound": formatted_flights,
        "return_flights": []
    })

"""
    
    new_content = pattern.sub(replacement, content)
    
    with open(r'd:\GS\SYSTEM-FRD-Airline\app.py', 'w', encoding='utf-8') as f:
        f.write(new_content)
        
    print("Replaced api_flights_search with DB insert!")

if __name__ == "__main__":
    rewrite_api_flights_search_with_db()
