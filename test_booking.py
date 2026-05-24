import urllib.request
import urllib.parse
import json

def test():
    # Login
    login_data = urllib.parse.urlencode({'username':'premium_agent', 'password':'agent123'}).encode()
    req = urllib.request.Request('http://127.0.0.1:5000/login', data=login_data)
    try:
        resp = urllib.request.urlopen(req)
        cookie = resp.headers.get('Set-Cookie')
        if not cookie:
            print("No cookie received")
            return
    except Exception as e:
        print("Login failed:", e)
        return

    # Book
    payload = {
        'flight_id': 1, 
        'passenger_name': 'Test Passenger', 
        'seat_number': '1A', 
        'payment_method': 'card'
    }
    headers = {
        'Content-Type': 'application/json',
        'Cookie': cookie
    }
    req2 = urllib.request.Request('http://127.0.0.1:5000/api/flights/book', data=json.dumps(payload).encode(), headers=headers)
    try:
        resp2 = urllib.request.urlopen(req2)
        print("Success:", resp2.read().decode())
    except urllib.error.HTTPError as e:
        print("HTTP Error:", e.code)
        print("Response body:", e.read().decode())
    except Exception as e:
        print("Error:", e)

if __name__ == '__main__':
    test()
