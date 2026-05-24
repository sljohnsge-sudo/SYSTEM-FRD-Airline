import http.client
import urllib.parse
import json

def test():
    conn = http.client.HTTPConnection("127.0.0.1", 5000)
    
    # Login
    login_data = urllib.parse.urlencode({'username': 'premium_agent', 'password': 'agent123'})
    headers = {"Content-Type": "application/x-www-form-urlencoded"}
    conn.request("POST", "/login", login_data, headers)
    res = conn.getresponse()
    
    cookie = res.getheader("Set-Cookie")
    res.read() # consume response
    print("Cookie:", cookie)
    
    # Book
    payload = {
        'flight_id': 8, 
        'return_flight_id': 9,
        'passenger_name': 'Test Passenger', 
        'seat_number': '1A', 
        'return_seat_number': '1B',
        'payment_method': 'card',
        'ticket_now': True
    }
    headers = {
        "Content-Type": "application/json",
        "Cookie": cookie
    }
    conn.request("POST", "/api/flights/book", json.dumps(payload), headers)
    res2 = conn.getresponse()
    print("Status:", res2.status)
    print("Body:", res2.read().decode())

if __name__ == '__main__':
    test()
