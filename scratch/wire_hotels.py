import re

def wire_hotel_search():
    with open(r'd:\GS\SYSTEM-FRD-Airline\app.py', 'r', encoding='utf-8') as f:
        content = f.read()
        
    pattern = re.compile(r'(@app\.route\("/api/hotels/search", methods=\["GET"\]\)\ndef api_hotels_search\(\):.*?)(?=@app\.route\("/api/pnr/retrieve", methods=\["GET"\]\))', re.DOTALL)
    
    replacement = """@app.route("/api/hotels/search", methods=["GET"])
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

"""
    
    new_content = pattern.sub(replacement, content)
    
    with open(r'd:\GS\SYSTEM-FRD-Airline\app.py', 'w', encoding='utf-8') as f:
        f.write(new_content)
        
    print("Replaced api_hotels_search!")

if __name__ == "__main__":
    wire_hotel_search()
