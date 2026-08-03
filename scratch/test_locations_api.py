import sys
import os

sys.path.append(r'd:\GS\SYSTEM-FRD-Airline')

from services.travelport_service import TravelportService

def test_locations():
    tp = TravelportService()
    
    # Let's test a few keywords to see what the API returns
    test_keywords = ["LON", "CMB", "DXB", "A"]
    
    print("Testing Travelport Locations API...")
    
    for kw in test_keywords:
        print(f"\n--- Searching for: {kw} ---")
        res = tp.search_locations(kw)
        
        if not res["success"]:
            print(f"Error: {res.get('error')}")
            continue
            
        data = res.get("data", [])
        if isinstance(data, list):
            print(f"Returned {len(data)} results.")
            for i, item in enumerate(data[:3]):  # Print first 3
                code = item.get('iataCode') or item.get('address', {}).get('cityCode')
                name = item.get('name')
                print(f"  {i+1}. {code} - {name}")
            if len(data) > 3:
                print("  ...")
        elif isinstance(data, dict):
            # Sometimes API wraps in an object
            items = data.get("ReferenceData", []) or data.get("locations", [])
            print(f"Returned dict with keys: {list(data.keys())}")
            print(f"Found {len(items)} items inside.")
        else:
            print("Unknown data format:", type(data))

if __name__ == "__main__":
    test_locations()
