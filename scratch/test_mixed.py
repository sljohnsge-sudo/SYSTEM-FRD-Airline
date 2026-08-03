import urllib.request, json, base64

def test():
    client_id = 'ISpiYxWT8r1rfMCkKiHp4HsLpyOA1hz3'
    client_secret = 'C0Sdvh6SuXcVT7abfBNX4DPWIsok5heRmsd-6IZb-tYDSD60UZh5EgrjA5OcYkt0'
    auth_str = base64.b64encode(f'{client_id}:{client_secret}'.encode()).decode()
    req = urllib.request.Request('https://auth.pp.travelport.net/oauth/token', data=b'grant_type=client_credentials', headers={'Authorization': f'Basic {auth_str}'})
    token = json.loads(urllib.request.urlopen(req).read())['access_token']
    
    headers = {'Authorization': f'Bearer {token}', 'XAUTH_TRAVELPORT_ACCESSGROUP': '7C6A54F8-78FF-458E-909E-194900761899', 'Content-Type': 'application/json'}
    payload = json.dumps({
        "CatalogOfferingsQueryRequest": {
            "CatalogOfferingsRequest": [{
                "@type": "CatalogOfferingsRequestAir", 
                "offersPerPage": 2, 
                "PassengerCriteria": [{"passengerType": "ADT", "quantity": 1}], 
                "SearchCriteriaFlight": [{"origin": "CMB", "destination": "DXB", "departureDate": "2026-06-19"}]
            }]
        }
    }).encode('utf-8')
    
    try:
        req2 = urllib.request.Request('https://api.travelport.com/11/air/catalog/search/catalogproductofferings', data=payload, headers=headers)
        print(urllib.request.urlopen(req2).read().decode()[:100])
    except Exception as e:
        print('Error api.travelport.com:', getattr(e, 'read', lambda: b'')().decode() or e)

test()
