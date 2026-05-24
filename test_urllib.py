import urllib.request
import urllib.parse
import urllib.error
import json

def test():
    class NoRedirectHandler(urllib.request.HTTPRedirectHandler):
        def http_error_302(self, req, fp, code, msg, headers):
            infourl = urllib.response.addinfourl(fp, headers, req.full_url)
            infourl.status = code
            infourl.code = code
            return infourl
        http_error_301 = http_error_303 = http_error_307 = http_error_302

    opener = urllib.request.build_opener(NoRedirectHandler())
    
    login_data = urllib.parse.urlencode({'username':'premium_agent', 'password':'agent123'}).encode()
    req = urllib.request.Request('http://127.0.0.1:5000/login', data=login_data)
    
    try:
        resp = opener.open(req)
        cookie = resp.headers.get('Set-Cookie')
        print("Got cookie:", cookie)
    except Exception as e:
        print("Login failed:", e)
        return

    payload = {
        'flight_id': 1, 
        'passenger_name': 'Test Passenger', 
        'seat_number': '1A', 
        'payment_method': 'card',
        'active_booking_path': 'ticket'
    }
    headers = {
        'Content-Type': 'application/json',
        'Cookie': cookie
    }
    req2 = urllib.request.Request('http://127.0.0.1:5000/api/flights/book', data=json.dumps(payload).encode(), headers=headers)
    try:
        resp2 = opener.open(req2)
        print("Success:", resp2.read().decode())
    except urllib.error.HTTPError as e:
        print("HTTP Error:", e.code)
        print("Response body:", e.read().decode())
    except Exception as e:
        print("Error:", e)

if __name__ == '__main__':
    test()
