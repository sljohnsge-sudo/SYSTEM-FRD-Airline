import json

with open('scratch/flight_response.json', 'r', encoding='utf-8') as f:
    res = json.load(f)

tp_data = res.get("data", {})
formatted_flights = []

offerings = tp_data.get("CatalogProductOfferingsResponse", {}).get("CatalogProductOfferings", {}).get("CatalogProductOffering", [])
reference_list = tp_data.get("CatalogProductOfferingsResponse", {}).get("ReferenceList", [])

flights_ref_map = {}
for ref in reference_list:
    if ref.get("@type") == "Flight":
        flights_ref_map[ref.get("id")] = ref

for offering in offerings:
    try:
        # Get price
        best_price = offering.get("ProductBrandOptions", [{}])[0].get("ProductBrandOffering", [{}])[0].get("BestCombinablePrice", {})
        total_price_str = best_price.get("TotalPrice", 0)
        try:
            price_val = float(total_price_str)
            price_lkr = price_val * 1.0 # already in LKR for CMB searches
        except ValueError:
            price_lkr = 0.0

        # Get flights
        products = offering.get("ProductBrandOptions", [{}])[0].get("ProductBrandOffering", [{}])[0].get("Product", [])
        product_ref = products[0].get("productRef") if products else None
        
        # Where are FlightSegments located in CatalogProductOfferingsResponse?
        # Actually, let's look at flights_ref_map or where the segments are
        pass
    except Exception as e:
        print("Error parsing", e)

print(f"Parsed {len(offerings)} offerings")
