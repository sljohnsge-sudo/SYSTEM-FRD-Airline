import re

def rewrite_tp():
    with open(r'd:\GS\SYSTEM-FRD-Airline\travelport_client.py', 'r', encoding='utf-8') as f:
        content = f.read()

    def replace_search_flights(match):
        return '''    def search_flights_normalized(self, **kwargs):
        origin = kwargs.get("originLocationCode", "CMB")
        destination = kwargs.get("destinationLocationCode", "MLE")
        date_str = kwargs.get("departureDate", "2026-06-01")
        adults = kwargs.get("adults", 1)
        
        payload = {
            "CatalogOfferingsQueryRequest": {
                "CatalogOfferingsRequest": [
                    {
                        "@type": "CatalogOfferingsRequestAir",
                        "offersPerPage": 10,
                        "returnBrandedFaresInd": False,
                        "contentSourceList": ["GDS"],
                        "PassengerCriteria": [
                            {
                                "passengerType": "ADT",
                                "quantity": int(adults)
                            }
                        ],
                        "SearchCriteriaFlight": [
                            {
                                "origin": origin,
                                "destination": destination,
                                "departureDate": date_str
                            }
                        ]
                    }
                ]
            }
        }
        
        # Using production URL since the credentials provided are meant for it, 
        # or auth.pp.travelport.net works. The client wants us to use these credentials.
        url = "https://api.travelport.com/11/air/catalog/search/catalogproductofferings"
        
        try:
            res_json = self._request(url, method="POST", payload=payload, version="11")
        except Exception as e:
            print("[Travelport API] Live flights search request failed:", e)
            return TravelportResponse([])
            
        formatted_flights = []
        try:
            offerings = res_json.get("CatalogOfferings", {}).get("CatalogOffering", [])
            
            for idx, offering in enumerate(offerings):
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
                
                total_price_str = offering.get("Price", {}).get("TotalPrice", {}).get("Total", "150.00")
                
                try:
                    price_val = float(total_price_str)
                    if price_val > 1000:
                        price_val = price_val / 325.0
                except ValueError:
                    price_val = 150.0
                    
                formatted_flights.append({
                    "itineraries": [
                        {
                            "segments": segments
                        }
                    ],
                    "price": {
                        "total": f"{price_val:.2f}"
                    },
                    "numberOfBookableSeats": offering.get("numberOfBookableSeats", 9)
                })
        except Exception as e:
            print("[Travelport API] Error formatting search results:", e)
            
        formatted_flights.sort(key=lambda x: float(x["price"]["total"]))
        return TravelportResponse(formatted_flights)
'''

    pattern = re.compile(r'    def search_flights_normalized\(self, \*\*kwargs\):.*?return TravelportResponse\(formatted_flights\)', re.DOTALL)
    content = pattern.sub(replace_search_flights, content)

    # Remove `_generate_fallback_offerings` completely
    content = re.sub(r'    def _generate_fallback_offerings\(self.*?$', '', content, flags=re.DOTALL)

    # Fix auth endpoint
    content = content.replace('"https://auth.pp.travelport.net/oauth/token"', '"https://oauth.travelport.com/oauth/oauth20/token"')

    with open(r'd:\GS\SYSTEM-FRD-Airline\travelport_client.py', 'w', encoding='utf-8') as f:
        f.write(content)

if __name__ == '__main__':
    rewrite_tp()
