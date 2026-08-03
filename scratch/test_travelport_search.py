import urllib.request
import urllib.parse
import json
import base64
import gzip

def get_token():
    username = "TP22497906"
    password = "XgxNZ9Fm"
    client_id = "ISpiYxWT8r1rfMCkKiHp4HsLpyOA1hz3"
    client_secret = "C0Sdvh6SuXcVT7abfBNX4DPWIsok5heRmsd-6IZb-tYDSD60UZh5EgrjA5OcYkt0"
    url = "https://auth.pp.travelport.net/oauth/token"
    
    auth_str = f"{client_id}:{client_secret}"
    encoded_auth = base64.b64encode(auth_str.encode()).decode()
    
    data = urllib.parse.urlencode({
        'grant_type': 'client_credentials',
        'username': username,
        'password': password
    }).encode('utf-8')
    
    req = urllib.request.Request(
        url,
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

def search_flights():
    token = get_token()
    print("Obtained token successfully.")
    
    # Pre-production URL
    url = "https://api.pp.travelport.net/11/air/catalog/search/catalogproductofferings"
    
    # Request Payload
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
        'TVP-PCC-CORE': '79G2_1G',
        'Accept-Version': '11',
        'Content-Version': '11',
        'Accept-Encoding': 'gzip, deflate',
        'Cache-Control': 'no-cache',
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
        with urllib.request.urlopen(req, timeout=15) as response:
            res_headers = response.info()
            res_body_bytes = response.read()
            
            # Decompress if gzipped
            if res_headers.get('Content-Encoding') == 'gzip':
                res_body = gzip.decompress(res_body_bytes).decode('utf-8')
            else:
                res_body = res_body_bytes.decode('utf-8')
                
            print("Response Status:", response.status)
            res_json = json.loads(res_body)
            # Write response to file to inspect it
            with open("scratch/search_response.json", "w") as f:
                json.dump(res_json, f, indent=2)
            print("Saved response to scratch/search_response.json")
            
            # Print brief summary of findings
            offerings = res_json.get("CatalogOfferings", {}).get("CatalogOffering", [])
            print("Number of CatalogOfferings returned:", len(offerings))
            if offerings:
                print("First offering details:")
                print(json.dumps(offerings[0], indent=2)[:500])
    except Exception as e:
        print("Search API Failed:", e)
        if hasattr(e, 'read'):
            err_headers = e.info()
            err_bytes = e.read()
            if err_headers.get('Content-Encoding') == 'gzip':
                err_body = gzip.decompress(err_bytes).decode('utf-8')
            else:
                err_body = err_bytes.decode('utf-8')
            print("Error details:", err_body)

if __name__ == "__main__":
    search_flights()
