with open(r'd:\GS\SYSTEM-FRD-Airline\app.py', 'r', encoding='utf-8') as f:
    content = f.read()

start_marker = '    tp_data = response["data"]'
end_marker = '            formatted_flights.append({'
start_idx = content.find(start_marker)
end_idx = content.find(end_marker, start_idx)

new_logic = '''    tp_data = response["data"]
    formatted_flights = []
    
    # Check for the new v11/v12 CatalogProductOfferingsResponse structure
    if "CatalogProductOfferingsResponse" in tp_data:
        root = tp_data.get("CatalogProductOfferingsResponse", {})
        offerings = root.get("CatalogProductOfferings", {}).get("CatalogProductOffering", [])
        
        # Build flights reference map
        flights_ref_map = {}
        for item in root.get('ReferenceList', []):
            if item.get('@type') == 'ReferenceListFlight':
                for f in item.get('Flight', []):
                    flights_ref_map[f.get('id')] = f
                    
        conn = get_db_connection()
        cursor = conn.cursor()
        
        for idx, offering in enumerate(offerings):
            try:
                # Get price
                best_price_info = offering.get("ProductBrandOptions", [{}])[0].get("ProductBrandOffering", [{}])[0].get("BestCombinablePrice", {})
                total_price_str = best_price_info.get("TotalPrice", "0")
                try:
                    price_lkr = float(total_price_str)
                except ValueError:
                    price_lkr = 0.0
                    
                # Get flight segments
                flight_refs = offering.get("ProductBrandOptions", [{}])[0].get("flightRefs", [])
                segments = []
                for ref in flight_refs:
                    seg = flights_ref_map.get(ref)
                    if seg:
                        segments.append({
                            "carrierCode": seg.get("carrier"),
                            "number": seg.get("number"),
                            "departure": {
                                "at": f"{seg.get('Departure', {}).get('date')}T{seg.get('Departure', {}).get('time')}"
                            },
                            "arrival": {
                                "at": f"{seg.get('Arrival', {}).get('date')}T{seg.get('Arrival', {}).get('time')}"
                            }
                        })
                
                if not segments:
                    continue
                    
                airline = segments[0]["carrierCode"]
                flight_number = f"{segments[0]['carrierCode']}-{segments[0]['number']}"
                dept_time = segments[0]["departure"]["at"].replace('T', ' ')[:19]
                arr_time = segments[-1]["arrival"]["at"].replace('T', ' ')[:19]
                seats_avail = 9
                segment_count = len(segments)
                
                # Save to DB so it can be booked
                cursor.execute("SELECT id FROM flights WHERE flight_number = %s AND departure_time = %s", (flight_number, dept_time))
                row = cursor.fetchone()
                if row:
                    flight_id = row[0]
                else:
                    cursor.execute("""
                        INSERT INTO flights (flight_number, airline, origin, destination, departure_time, arrival_time, price, seats_available, flight_type, segment_count)
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, 'GDS', %s)
                    """, (flight_number, airline, origin, destination, dept_time, arr_time, price_lkr, seats_avail, segment_count))
                    flight_id = cursor.lastrowid
                
'''

# Wait, there's a fallback to the old structure needed just in case?
# Well, they are using v11 everywhere so it's always the new structure.
# But let's just replace the whole block from start_marker to end_marker!

content = content[:start_idx] + new_logic + content[end_idx:]

with open(r'd:\GS\SYSTEM-FRD-Airline\app.py', 'w', encoding='utf-8') as f:
    f.write(content)
print("Updated app.py with new parsing logic.")
