import random
import datetime

class MockResponse:
    def __init__(self, data):
        self.data = data

class MockLocations:
    def __init__(self):
        self.popular_locations = [
            {"city": "Colombo", "code": "CMB", "name": "Bandaranaike Intl Arpt", "country": "SRI LANKA", "country_code": "LK"},
            {"city": "Jaffna", "code": "JAF", "name": "Jaffna Intl Arpt", "country": "SRI LANKA", "country_code": "LK"},
            {"city": "Delhi", "code": "DEL", "name": "Delhi Indira Gandhi Intl", "country": "INDIA", "country_code": "IN"},
            {"city": "Chennai", "code": "MAA", "name": "Chennai Arpt", "country": "INDIA", "country_code": "IN"},
            {"city": "Mumbai", "code": "BOM", "name": "Chhatrapati Shivaji Maharaj Intl", "country": "INDIA", "country_code": "IN"},
            {"city": "Bangalore", "code": "BLR", "name": "Kempegowda Intl", "country": "INDIA", "country_code": "IN"},
            {"city": "Singapore", "code": "SIN", "name": "Changi Arpt", "country": "SINGAPORE", "country_code": "SG"},
            {"city": "Male", "code": "MLE", "name": "Velana Intl Arpt", "country": "MALDIVES", "country_code": "MV"},
            {"city": "London", "code": "LHR", "name": "London Heathrow Arpt", "country": "UNITED KINGDOM", "country_code": "GB"},
            {"city": "London", "code": "LGW", "name": "London Gatwick Arpt", "country": "UNITED KINGDOM", "country_code": "GB"},
            {"city": "Dubai", "code": "DXB", "name": "Dubai Intl Arpt", "country": "UNITED ARAB EMIRATES", "country_code": "AE"},
            {"city": "Abu Dhabi", "code": "AUH", "name": "Abu Dhabi Intl Arpt", "country": "UNITED ARAB EMIRATES", "country_code": "AE"},
            {"city": "Doha", "code": "DOH", "name": "Hamad Intl Arpt", "country": "QATAR", "country_code": "QA"},
            {"city": "Sydney", "code": "SYD", "name": "Sydney Kingsford Smith Arpt", "country": "AUSTRALIA", "country_code": "AU"},
            {"city": "Melbourne", "code": "MEL", "name": "Melbourne Arpt", "country": "AUSTRALIA", "country_code": "AU"},
            {"city": "New York", "code": "JFK", "name": "John F. Kennedy Intl", "country": "UNITED STATES", "country_code": "US"},
            {"city": "New York", "code": "LGA", "name": "LaGuardia Arpt", "country": "UNITED STATES", "country_code": "US"},
            {"city": "Newark", "code": "EWR", "name": "Newark Liberty Intl", "country": "UNITED STATES", "country_code": "US"},
            {"city": "Paris", "code": "CDG", "name": "Charles de Gaulle Arpt", "country": "FRANCE", "country_code": "FR"},
            {"city": "Frankfurt", "code": "FRA", "name": "Frankfurt Arpt", "country": "GERMANY", "country_code": "DE"},
            {"city": "Munich", "code": "MUC", "name": "Munich Arpt", "country": "GERMANY", "country_code": "DE"},
            {"city": "Rome", "code": "FCO", "name": "Leonardo da Vinci-Fiumicino Arpt", "country": "ITALY", "country_code": "IT"},
            {"city": "Zurich", "code": "ZRH", "name": "Zurich Arpt", "country": "SWITZERLAND", "country_code": "CH"},
            {"city": "Tokyo", "code": "HND", "name": "Haneda Arpt", "country": "JAPAN", "country_code": "JP"},
            {"city": "Tokyo", "code": "NRT", "name": "Narita Intl Arpt", "country": "JAPAN", "country_code": "JP"},
            {"city": "Kuala Lumpur", "code": "KUL", "name": "Kuala Lumpur Intl", "country": "MALAYSIA", "country_code": "MY"},
            {"city": "Bangkok", "code": "BKK", "name": "Suvarnabhumi Arpt", "country": "THAILAND", "country_code": "TH"},
            {"city": "Riyadh", "code": "RUH", "name": "King Khalid Intl Arpt", "country": "SAUDI ARABIA", "country_code": "SA"},
            {"city": "Jeddah", "code": "JED", "name": "King Abdulaziz Intl Arpt", "country": "SAUDI ARABIA", "country_code": "SA"},
            {"city": "Beijing", "code": "PEK", "name": "Beijing Capital Intl", "country": "CHINA", "country_code": "CN"},
            {"city": "Toronto", "code": "YYZ", "name": "Toronto Pearson Intl", "country": "CANADA", "country_code": "CA"}
        ]

    def get(self, keyword, subType=None):
        q = keyword.upper().strip()
        results = []
        for item in self.popular_locations:
            # Match code, city or country name
            if q in item["code"] or q in item["city"].upper() or q in item["country"].upper():
                results.append({
                    "iataCode": item["code"],
                    "name": item["name"],
                    "address": {
                        "cityCode": item["code"],
                        "cityName": item["city"],
                        "countryCode": item["country_code"],
                        "countryName": item["country"]
                    }
                })
        return MockResponse(results)

class MockHotelsByCity:
    def get(self, cityCode):
        c_code = cityCode.upper()
        # Predefined mock hotels mapped to common search cities
        hotel_database = {
            "CMB": [
                "Cinnamon Grand Colombo", "Shangri-La Colombo", "Galle Face Hotel", "Marine Drive Palace", "Hilton Colombo"
            ],
            "MLE": [
                "Kurumba Maldives Resort", "Centara Ras Fushi Resort", "Bandos Maldives", "Velassaru Maldives", "Paradise Island Resort"
            ],
            "LHR": [
                "Sofitel London Heathrow", "Hilton London Heathrow Airport", "Radisson Blu Heathrow", "Sheraton Skyline Heathrow", "Renaissance London Heathrow"
            ],
            "SIN": [
                "Marina Bay Sands", "Raffles Hotel Singapore", "Changi Village Inn", "Pan Pacific Singapore", "Carlton Hotel Singapore"
            ],
            "DXB": [
                "Burj Al Arab Jumeirah", "Atlantis The Palm", "Jumeirah Beach Hotel", "Address Downtown Dubai", "Grand Hyatt Dubai"
            ]
        }
        
        hotel_names = hotel_database.get(c_code, [
            f"Grand Regency {c_code}",
            f"{c_code} Palace Hotel",
            f"Royal Orchid {c_code} Resort",
            f"Standard Central {c_code} Hotel",
            f"Charming Boutique Inn {c_code}"
        ])
        
        results = []
        for name in hotel_names:
            results.append({
                "name": name,
                "address": {
                    "cityName": c_code,
                    "countryCode": "US" # generic country fallback
                }
            })
        return MockResponse(results)

class MockReferenceDataHotels:
    def __init__(self):
        self.by_city = MockHotelsByCity()

class MockReferenceData:
    def __init__(self):
        self.locations = MockLocations()
        self.locations.hotels = MockReferenceDataHotels()

class MockFlightOffersSearch:
    def get(self, **kwargs):
        origin = kwargs.get("originLocationCode", "CMB")
        destination = kwargs.get("destinationLocationCode", "MLE")
        date_str = kwargs.get("departureDate", "2026-06-01")
        
        try:
            dept_date = datetime.datetime.strptime(date_str, "%Y-%m-%d").date()
        except ValueError:
            dept_date = datetime.date.today() + datetime.timedelta(days=2)
            
        airlines = ['UL', 'EK', 'QR', 'SQ', '6E', 'BA', 'EY', 'MH', 'TG', 'CX']
        results = []
        
        # Generate 10 mock flight offers
        for i in range(10):
            carrier = random.choice(airlines)
            flight_num = str(random.randint(100, 999))
            
            # Staggered departure times
            dept_hour = (i * 2 + 6) % 24
            dept_min = random.choice([0, 15, 30, 45])
            dept_time = datetime.datetime.combine(dept_date, datetime.time(dept_hour, dept_min))
            
            # Flight duration based on route or randomly generated
            flight_duration = random.randint(1, 12)
            arr_time = dept_time + datetime.timedelta(hours=flight_duration, minutes=random.choice([0, 15, 30, 45]))
            
            # Flight price in EUR (which app.py converts by multiplying by 325)
            # Standard GDS prices in USD/EUR are 150-700
            price_eur = round(random.uniform(130.0, 580.0), 2)
            
            # Layover segment count
            seg_count = 1 if flight_duration < 4 else random.randint(1, 2)
            
            segments = []
            current_dept = dept_time
            for s in range(seg_count):
                seg_duration = flight_duration // seg_count
                current_arr = current_dept + datetime.timedelta(hours=seg_duration)
                
                segments.append({
                    "carrierCode": carrier,
                    "number": flight_num,
                    "departure": {
                        "at": current_dept.strftime("%Y-%m-%dT%H:%M:%S")
                    },
                    "arrival": {
                        "at": current_arr.strftime("%Y-%m-%dT%H:%M:%S")
                    }
                })
                current_dept = current_arr + datetime.timedelta(hours=random.randint(1, 2))
                
            results.append({
                "itineraries": [
                    {
                        "segments": segments
                    }
                ],
                "price": {
                    "total": str(price_eur)
                },
                "numberOfBookableSeats": random.randint(3, 9)
            })
            
        # Sort results by price total ascending (like a real GDS API usually behaves)
        results.sort(key=lambda x: float(x["price"]["total"]))
        return MockResponse(results)

class MockShopping:
    def __init__(self):
        self.flight_offers_search = MockFlightOffersSearch()

class MockGDSClient:
    def __init__(self, **kwargs):
        self.reference_data = MockReferenceData()
        self.shopping = MockShopping()
