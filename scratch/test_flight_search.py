import sys
import os

sys.path.append(r'd:\GS\SYSTEM-FRD-Airline')

from services.travelport_service import TravelportService
import json

def test_flight_search():
    tp = TravelportService()
    
    print("Testing Travelport Flight Search API...")
    
    # Example search: CMB to DXB on 2026-06-19
    res = tp.search_flights("CMB", "DXB", "2026-06-19", 1)
    
    if not res["success"]:
        print(f"Error: {res.get('error')}")
    else:
        data = res.get("data", {})
        print(f"Success! Returned data keys: {list(data.keys())}")
        print("Data Snippet:")
        print(json.dumps(data, indent=2)[:1000])

if __name__ == "__main__":
    test_flight_search()
