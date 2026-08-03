import re

def remove_flight_api():
    with open(r'd:\GS\SYSTEM-FRD-Airline\app.py', 'r', encoding='utf-8') as f:
        content = f.read()
        
    # Remove imports and initialization
    content = re.sub(r'from travelport_client import TravelportClient\n+', '', content)
    content = re.sub(r'flight_api = TravelportClient\([^)]+\)\n+', '', content)
    
    # Update resolve_iata_code
    pattern = re.compile(r'def resolve_iata_code\(keyword, flight_api_client=None\):.*?return None', re.DOTALL)
    
    replacement = """def resolve_iata_code(keyword, flight_api_client=None):
    if len(keyword) == 3 and keyword.isalpha():
        return keyword.upper()
        
    from services.travelport_service import TravelportService
    tp_service = TravelportService()
    
    try:
        response = tp_service.search_locations(keyword)
        if response["success"] and response.get("data"):
            data = response["data"]
            if isinstance(data, list) and len(data) > 0:
                return data[0].get('iataCode') or data[0].get('address', {}).get('cityCode')
    except Exception as e:
        print(f"Error resolving location '{keyword}':", e)
    return None"""
    
    content = pattern.sub(replacement, content)
    
    # Remove flight_api from search_flights calls since it was refactored
    content = content.replace("origin = resolve_iata_code(origin_input, flight_api)", "origin = resolve_iata_code(origin_input)")
    content = content.replace("destination = resolve_iata_code(destination_input, flight_api)", "destination = resolve_iata_code(destination_input)")

    with open(r'd:\GS\SYSTEM-FRD-Airline\app.py', 'w', encoding='utf-8') as f:
        f.write(content)
        
    print("Removed flight_api!")

if __name__ == "__main__":
    remove_flight_api()
