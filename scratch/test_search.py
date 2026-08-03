from services.travelport_service import TravelportService
import json

svc = TravelportService()
res = svc.search_flights("CMB", "MLE", "2026-06-16", 1)
print(json.dumps(res, indent=2))
