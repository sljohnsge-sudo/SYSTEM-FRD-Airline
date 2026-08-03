import re

def rewrite_api_flights_search():
    with open(r'd:\GS\SYSTEM-FRD-Airline\app.py', 'r', encoding='utf-8') as f:
        content = f.read()
        
    # We want to replace the entire api_flights_search function.
    # It starts at: @app.route("/api/flights/search", methods=["GET"])
    # And ends before: @app.route("/api/flights/seat-availability", methods=["POST"])
    
    pattern = re.compile(r'(@app\.route\("/api/flights/search", methods=\["GET"\]\)\ndef api_flights_search\(\):.*?)(?=@app\.route\("/api/flights/seat-availability", methods=\["POST"\]\))', re.DOTALL)
    
    replacement = """@app.route("/api/flights/search", methods=["GET"])
def api_flights_search():
    from services.travelport_service import TravelportService
    
    origin = request.args.get("origin", "").strip()
    destination = request.args.get("destination", "").strip()
    date_str = request.args.get("date", "").strip()
    adults = request.args.get("adults", "1").strip()
    
    # We will use Travelport directly and only Travelport
    tp_service = TravelportService()
    
    response = tp_service.search_flights(origin, destination, date_str, adults=adults)
    
    if not response["success"]:
        return jsonify({"success": False, "error": response.get("error", "Failed to search flights on Travelport API.")})
        
    # Travelport Service returns data according to Travelport format.
    # We need to format it to standard app format here or in the service.
    # We did not fully implement formatting in TravelportService yet.
    # We will just parse the TravelportResponse to the format expected by the frontend.
    
    tp_data = response["data"]
    formatted_flights = []
    
    offerings = tp_data.get("CatalogOfferings", {}).get("CatalogOffering", [])
    
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
                # Convert EUR to LKR (approx 325 exchange rate) for consistency if Travelport returns USD/EUR
                price_lkr = price_val * 325.0
            except ValueError:
                price_lkr = 0.0
                
            formatted_flights.append({
                "id": idx + 1000, # Fake ID since we aren't saving to DB immediately
                "airline": segments[0]["carrierCode"] if segments else "Unknown",
                "flight_number": f"{segments[0]['carrierCode']}-{segments[0]['number']}" if segments else "Unknown",
                "origin": origin,
                "destination": destination,
                "departure_time": segments[0]["departure"]["at"].replace('T', ' ')[:19] if segments else "",
                "arrival_time": segments[-1]["arrival"]["at"].replace('T', ' ')[:19] if segments else "",
                "price": price_lkr,
                "seats_available": offering.get("numberOfBookableSeats", 9),
                "flight_type": "GDS",
                "gds_source": "Travelport",
                "segment_count": len(segments)
            })
        except Exception as e:
            print("Error parsing flight:", e)
            
    # Return formatted flights directly without DB storage
    return jsonify({
        "success": True,
        "outbound": formatted_flights,
        "return_flights": []
    })

"""
    
    new_content = pattern.sub(replacement, content)
    
    with open(r'd:\GS\SYSTEM-FRD-Airline\app.py', 'w', encoding='utf-8') as f:
        f.write(new_content)
        
    print("Replaced api_flights_search!")

if __name__ == "__main__":
    rewrite_api_flights_search()
