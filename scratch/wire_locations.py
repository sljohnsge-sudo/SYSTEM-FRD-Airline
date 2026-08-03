import re

def wire_location_search():
    with open(r'd:\GS\SYSTEM-FRD-Airline\app.py', 'r', encoding='utf-8') as f:
        content = f.read()
        
    pattern = re.compile(r'(@app\.route\("/api/locations/search", methods=\["GET"\]\)\ndef api_locations_search\(\):.*?)(?=@app\.route\("/api/flights/search", methods=\["GET"\]\))', re.DOTALL)
    
    replacement = """@app.route("/api/locations/search", methods=["GET"])
def api_locations_search():
    q = request.args.get("q", "").strip().upper()
    
    if not q or len(q) < 2:
        return jsonify({"success": True, "groups": []})
        
    from services.travelport_service import TravelportService
    tp_service = TravelportService()
    
    response = tp_service.search_locations(q)
    
    if not response["success"]:
        return jsonify({"success": False, "error": response.get("error", "Location search failed")})
        
    matches = []
    seen_codes = set()
    
    tp_data = response.get("data", [])
    
    for item in tp_data:
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
            
        matches.append({
            "city": city_name,
            "code": code,
            "name": f"{airport_name} Arpt" if "Airport" not in airport_name and "Intl" not in airport_name else airport_name,
            "country": country_name,
            "country_code": country_code
        })
        seen_codes.add(code)
        
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

"""
    
    new_content = pattern.sub(replacement, content)
    
    with open(r'd:\GS\SYSTEM-FRD-Airline\app.py', 'w', encoding='utf-8') as f:
        f.write(new_content)
        
    print("Replaced api_locations_search!")

if __name__ == "__main__":
    wire_location_search()
