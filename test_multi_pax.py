import requests
import json

# Test 1: Verify flight search returns quickly with real pricing
print("--- Test 1: Flight Search (CMB to MEL) ---")
try:
    r = requests.get(
        "http://127.0.0.1:5000/api/flights/search?origin=CMB&destination=MEL&date=2026-06-10&flight_type=ALL",
        timeout=10
    )
    data = r.json()
    flights = data.get("flights", [])
    print(f"Status: {r.status_code} | Success: {data.get('success')} | Flights returned: {len(flights)}")
    
    if flights:
        f = flights[0]
        price = float(f["price"])
        print(f"First flight: {f['airline']} | Flight No: {f['flight_number']}")
        print(f"Raw DB price: {price}")
        print(f"1 pax display price: LKR {price * 1:,.0f}")
        print(f"3 pax display price: LKR {price * 3:,.0f}")
        print(f"3 pax backend total_price (with markup): LKR {price * 3 + 15 * 3:,.2f}")

except Exception as e:
    print(f"Error: {e}")

# Test 2: Simulate a B2C booking for 3 passengers and check what total_price gets stored
print("\n--- Test 2: Verify booking payload would compute correct total_price ---")
# The backend formula (app.py lines 960-964) is:
# orig_price = flight["price"] * pax_count
# total_price = orig_price + markup * pax_count
# For mock flights with LKR prices e.g., 90000 LKR:
mock_price = 90000  # typical mock LKR price
pax = 3
markup = 15
backend_total = mock_price * pax + markup * pax
print(f"Mock flight price (LKR): {mock_price}")
print(f"Backend stored total_price for {pax} pax: LKR {backend_total:,.2f}")
print(f"My Bookings page would display: LKR {backend_total:,.2f}")
print(f"Frontend displays (price * travelers): LKR {mock_price * pax:,.0f}")
print(f"Difference (just service fee): LKR {backend_total - mock_price * pax:,.2f}")
print("\nConclusion: If prices are in LKR, My Bookings should display the correct amount.")
