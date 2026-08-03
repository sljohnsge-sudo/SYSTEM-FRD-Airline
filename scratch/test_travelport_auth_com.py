import urllib.request
import urllib.parse
import json
import base64

def get_token(auth_url):
    username = "TP22497906"
    password = "XgxNZ9Fm"
    client_id = "ISpiYxWT8r1rfMCkKiHp4HsLpyOA1hz3"
    client_secret = "C0Sdvh6SuXcVT7abfBNX4DPWIsok5heRmsd-6IZb-tYDSD60UZh5EgrjA5OcYkt0"
    
    auth_str = f"{client_id}:{client_secret}"
    encoded_auth = base64.b64encode(auth_str.encode()).decode()
    
    data = urllib.parse.urlencode({
        'grant_type': 'client_credentials',
        'username': username,
        'password': password
    }).encode('utf-8')
    
    req = urllib.request.Request(
        auth_url,
        data=data,
        headers={
            'Authorization': f'Basic {encoded_auth}',
            'Content-Type': 'application/x-www-form-urlencoded',
            'Accept': 'application/json'
        }
    )
    with urllib.request.urlopen(req, timeout=10) as response:
        res = json.loads(response.read().decode())
        return res['access_token']

def main():
    auth_urls = [
        "https://auth.pp.travelport.com/oauth/token",
        "https://oauth.pp.travelport.com/oauth/oauth20/token",
        "https://auth.pp.travelport.net/oauth/token"
    ]
    
    for url in auth_urls:
        print(f"Testing Auth URL: {url}")
        try:
            token = get_token(url)
            print("  SUCCESS! Obtained Token.")
            # Now let's try using this token against api.pp.travelport.com
            test_search(token)
        except Exception as e:
            print("  FAILED:", e)

def test_search(token):
    url = "https://api.pp.travelport.com/11/air/catalog/search/catalogproductofferings"
    payload = {
      "CatalogOfferingsQueryRequest": {
        "CatalogOfferingsRequest": [
          {
            "@type": "CatalogOfferingsRequestAir",
            "offersPerPage": 5,
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
                "destination": "DEL",
                "departureDate": "2026-07-20"
              }
            ]
          }
        ]
      }
    }
    
    headers = {
        'Authorization': f'Bearer {token}',
        'XAUTH_TRAVELPORT_ACCESSGROUP': '7C6A54F8-78FF-458E-909E-194900761899',
        'Accept-Version': '11',
        'Content-Version': '11',
        'Content-Type': 'application/json',
        'Accept': 'application/json'
    }
    
    req = urllib.request.Request(
        url,
        data=json.dumps(payload).encode('utf-8'),
        headers=headers,
        method='POST'
    )
    
    try:
        with urllib.request.urlopen(req, timeout=10) as response:
            print("    Search Success status:", response.status)
    except Exception as e:
        if hasattr(e, 'read'):
            print("    Search Failed:", e.read().decode())
        else:
            print("    Search Failed:", e)

if __name__ == "__main__":
    main()
