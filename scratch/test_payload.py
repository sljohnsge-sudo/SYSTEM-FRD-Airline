from services.travelport_service import TravelportService
import json

svc = TravelportService()
payload = {
  "CatalogOfferingsQueryRequest": {
    "CatalogOfferingsRequest": [
      {
        "@type": "CatalogOfferingsRequestAir",
        "offersPerPage": 20,
        "returnBrandedFaresInd": False,
        "contentSourceList": ["GDS"],
        "PassengerCriteria": [
          {
            "passengerType": "ADT",
            "quantity": 1
          }
        ],
        "SearchCriteriaFlight": [
          {
            "origin": "CMB",
            "destination": "MLE",
            "departureDate": "2026-06-16"
          }
        ]
      }
    ]
  }
}
res = svc._make_request('/11/air/catalog/search/catalogproductofferings', payload=payload)
print("Success:", res.get("success"))
if res.get("success"):
    print("Keys:", res["data"].keys())
else:
    print("Error:", res)
