import urllib.request
import urllib.parse
import json
import base64
import gzip

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

def test_endpoint(name, auth_url, search_url):
    print(f"\n========================================")
    print(f"Testing Environment: {name}")
    print(f"Auth URL: {auth_url}")
    print(f"Search URL: {search_url}")
    print(f"========================================")
    
    try:
        token = get_token(auth_url)
        print("Token obtained successfully.")
    except Exception as e:
        print("Failed to get token:", e)
        if hasattr(e, 'read'):
            print("Token error details:", e.read().decode())
        return
        
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
        'Accept-Encoding': 'gzip, deflate',
        'Cache-Control': 'no-cache',
        'Content-Type': 'application/json',
        'Accept': 'application/json'
    }
    
    req = urllib.request.Request(
        search_url,
        data=json.dumps(payload).encode('utf-8'),
        headers=headers,
        method='POST'
    )
    
    try:
        with urllib.request.urlopen(req, timeout=15) as response:
            res_headers = response.info()
            res_body_bytes = response.read()
            if res_headers.get('Content-Encoding') == 'gzip':
                res_body = gzip.decompress(res_body_bytes).decode('utf-8')
            else:
                res_body = res_body_bytes.decode('utf-8')
            print("Search Response Status:", response.status)
            res_json = json.loads(res_body)
            offerings = res_json.get("CatalogOfferings", {}).get("CatalogOffering", [])
            print("SUCCESS! Number of offerings returned:", len(offerings))
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

def main():
    endpoints_to_test = [
        # Pre-prod options
        {
            "name": "Pre-prod .com",
            "auth": "https://auth.pp.travelport.net/oauth/token",
            "search": "https://api.pp.travelport.com/11/air/catalog/search/catalogproductofferings"
        },
        {
            "name": "Pre-prod .net",
            "auth": "https://auth.pp.travelport.net/oauth/token",
            "search": "https://api.pp.travelport.net/11/air/catalog/search/catalogproductofferings"
        },
        # Production options
        {
            "name": "Production .com",
            "auth": "https://auth.pp.travelport.net/oauth/token", # try PP auth with prod search
            "search": "https://api.travelport.com/11/air/catalog/search/catalogproductofferings"
        },
        {
            "name": "Production .net",
            "auth": "https://auth.pp.travelport.net/oauth/token", # try PP auth with prod search
            "search": "https://api.travelport.net/11/air/catalog/search/catalogproductofferings"
        }
    ]
    
    for item in endpoints_to_test:
        test_endpoint(item["name"], item["auth"], item["search"])

if __name__ == "__main__":
    main()
