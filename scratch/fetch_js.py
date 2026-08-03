import urllib.request

url = "http://127.0.0.1:5000/static/js/main.js?v=1.0.5"
try:
    with urllib.request.urlopen(url) as response:
        html = response.read().decode('utf-8')
        
    # Let's find retrieveBookingByPNR
    idx = html.find("function retrieveBookingByPNR")
    if idx != -1:
        print("Found retrieveBookingByPNR at index", idx)
        # Print next 3000 chars
        print(html[idx:idx+3000])
    else:
        print("NOT FOUND retrieveBookingByPNR in served JS!")
except Exception as e:
    print("Error:", e)
