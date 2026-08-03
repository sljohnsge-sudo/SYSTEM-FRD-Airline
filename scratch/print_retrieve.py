filepath = r"d:\GS\SYSTEM-FRD-Airline\static\js\main.js"

with open(filepath, 'r', encoding='utf-8') as f:
    content = f.read()

idx = content.find("function retrieveBookingByPNR")
if idx != -1:
    print(content[idx : idx + 10000]) # Print up to 10k chars to cover the entire function
else:
    print("Not found")
