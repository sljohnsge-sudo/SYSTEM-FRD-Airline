import re

def add_static_iata_db():
    with open(r'd:\GS\SYSTEM-FRD-Airline\app.py', 'r', encoding='utf-8') as f:
        content = f.read()

    # Rewrite the locations API to use a static list
    pattern = re.compile(r'(@app\.route\("/api/locations/search", methods=\["GET"\]\)\ndef api_locations_search\(\):.*?)(?=@app\.route\("/api/flights/search", methods=\["GET"\]\))', re.DOTALL)
    
    replacement = """@app.route("/api/locations/search", methods=["GET"])
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

"""
    
    new_content = pattern.sub(replacement, content)
    
    with open(r'd:\GS\SYSTEM-FRD-Airline\app.py', 'w', encoding='utf-8') as f:
        f.write(new_content)
        
    print("Static Location DB restored!")

if __name__ == "__main__":
    add_static_iata_db()
