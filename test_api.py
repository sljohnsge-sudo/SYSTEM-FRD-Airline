from amadeus import Client
import traceback
amadeus = Client(client_id='3ZBEyT1bTUzMUPkcEPBUOEKIAkEjgu5o', client_secret='2K9Xh5GC2UF9rVo3', hostname='test')
try:
    response = amadeus.shopping.flight_offers_search.get(originLocationCode='CMB', destinationLocationCode='MLE', departureDate='2026-06-01', adults=1, max=5)
    print('Success:', len(response.data))
except Exception as e:
    traceback.print_exc()
