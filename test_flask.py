import sys
from app import app
with app.test_client() as client:
    response = client.get('/api/flights/search?origin=CMB&destination=MLE&date=2026-06-01')
    print(response.json)
