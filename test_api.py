from travelport_client import TravelportClient as Client
import traceback

# Initialize TravelportClient with credentials
travelport = Client(
    client_id='ISpiYxWT8r1rfMCkKiHp4HsLpyOA1hz3',
    client_secret='C0Sdvh6SuXcVT7abfBNX4DPWIsok5heRmsd-6IZb-tYDSD60UZh5EgrjA5OcYkt0',
    username='TP22497906',
    password='XgxNZ9Fm',
    access_group='7C6A54F8-78FF-458E-909E-194900761899',
    pcc='79G2'
)

try:
    print("Executing Travelport flight search...")
    response = travelport.shopping.flight_offers_search.get(
        originLocationCode='CMB', 
        destinationLocationCode='MLE', 
        departureDate='2026-06-16', 
        adults=1
    )
    print('Success! Flights returned:', len(response.data))
    if response.data:
        first = response.data[0]
        print("First Flight Offer:")
        print("  Price (EUR):", first['price']['total'])
        print("  Seats Available:", first['numberOfBookableSeats'])
        print("  Outbound Segments:")
        for seg in first['itineraries'][0]['segments']:
            print(f"    - {seg['carrierCode']}-{seg['number']} from {seg['departure']['at']} to {seg['arrival']['at']}")
except Exception as e:
    traceback.print_exc()
