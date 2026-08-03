import urllib.request
import urllib.parse
import json
import base64

def test_auth():
    # Credentials
    username = "TP22497906"
    password = "XgxNZ9Fm"
    client_id = "ISpiYxWT8r1rfMCkKiHp4HsLpyOA1hz3"
    client_secret = "C0Sdvh6SuXcVT7abfBNX4DPWIsok5heRmsd-6IZb-tYDSD60UZh5EgrjA5OcYkt0"
    access_group = "7C6A54F8-78FF-458E-909E-194900761899"
    
    # Try PP/Pre-prod endpoint first: https://auth.pp.travelport.net/oauth/token
    # According to Travelport documentation, for some systems the OAuth request body is:
    # grant_type=client_credentials or username/password with basic auth of client_id/client_secret
    
    endpoints = [
        "https://auth.pp.travelport.net/oauth/token",
        "https://oauth.travelport.com/oauth/oauth20/token"
    ]
    
    for url in endpoints:
        print(f"Testing Auth URL: {url}")
        
        # Method 1: standard oauth client credentials
        # We need to send Client ID and Secret in Basic Auth or Body
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
        
        try:
            with urllib.request.urlopen(req, timeout=10) as response:
                body = response.read().decode()
                print("Method 1 Success:", body)
                continue
        except Exception as e:
            print("Method 1 Failed:", e)
            if hasattr(e, 'read'):
                print("Error Details:", e.read().decode())
                
        # Method 2: Username & password in basic auth or plain credentials
        # Let's try basic auth with username and password
        auth_str_up = f"{username}:{password}"
        encoded_auth_up = base64.b64encode(auth_str_up.encode()).decode()
        data_2 = urllib.parse.urlencode({
            'grant_type': 'client_credentials',
            'client_id': client_id,
            'client_secret': client_secret
        }).encode('utf-8')
        
        req_2 = urllib.request.Request(
            url,
            data=data_2,
            headers={
                'Authorization': f'Basic {encoded_auth_up}',
                'Content-Type': 'application/x-www-form-urlencoded',
                'Accept': 'application/json'
            }
        )
        
        try:
            with urllib.request.urlopen(req_2, timeout=10) as response:
                body = response.read().decode()
                print("Method 2 Success:", body)
                continue
        except Exception as e:
            print("Method 2 Failed:", e)
            if hasattr(e, 'read'):
                print("Error Details:", e.read().decode())
                
        # Method 3: No basic auth, everything in JSON request body or URL-encoded body
        data_3 = urllib.parse.urlencode({
            'grant_type': 'client_credentials',
            'client_id': client_id,
            'client_secret': client_secret,
            'username': username,
            'password': password
        }).encode('utf-8')
        
        req_3 = urllib.request.Request(
            url,
            data=data_3,
            headers={
                'Content-Type': 'application/x-www-form-urlencoded',
                'Accept': 'application/json'
            }
        )
        
        try:
            with urllib.request.urlopen(req_3, timeout=10) as response:
                body = response.read().decode()
                print("Method 3 Success:", body)
                continue
        except Exception as e:
            print("Method 3 Failed:", e)
            if hasattr(e, 'read'):
                print("Error Details:", e.read().decode())

if __name__ == "__main__":
    test_auth()
