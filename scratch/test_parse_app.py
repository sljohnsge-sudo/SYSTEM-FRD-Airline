from services.travelport_service import TravelportService

tp_service = TravelportService()
response = tp_service.search_flights('CMB', 'MLE', '2026-06-16', 1)
tp_data = response["data"]

formatted_flights = []

print("Keys in tp_data:", tp_data.keys())

if "CatalogProductOfferingsResponse" in tp_data:
    root = tp_data.get("CatalogProductOfferingsResponse", {})
    offerings = root.get("CatalogProductOfferings", {}).get("CatalogProductOffering", [])
    
    print("Offerings count:", len(offerings))
    
    # Build flights reference map
    flights_ref_map = {}
    for item in root.get('ReferenceList', []):
        if item.get('@type') == 'ReferenceListFlight':
            for f in item.get('Flight', []):
                flights_ref_map[f.get('id')] = f
                
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
                print("No segments found for offering!")
                continue
                
            airline = segments[0]["carrierCode"]
            flight_number = f"{segments[0]['carrierCode']}-{segments[0]['number']}"
            dept_time = segments[0]["departure"]["at"].replace('T', ' ')[:19]
            arr_time = segments[-1]["arrival"]["at"].replace('T', ' ')[:19]
            seats_avail = 9
            segment_count = len(segments)
            
            formatted_flights.append({
                "airline": airline,
                "flight_number": flight_number,
                "price": price_lkr
            })
            
        except Exception as e:
            print("Error parsing flight:", e)

print("Formatted flights:", len(formatted_flights))
