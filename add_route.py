import os
path = r'd:\GS\SYSTEM-FRD-Airline\app.py'
with open(path, 'r', encoding='utf-8') as f:
    content = f.read()

route_code = '''
# Route: B2C Hotel Details
@app.route("/b2c/hotel-details")
def b2c_hotel_details():
    return render_template("b2c_hotel_details.html")

'''

if 'def b2c_hotel_details():' not in content:
    content = content.replace('if __name__ == "__main__":', route_code + 'if __name__ == "__main__":')
    with open(path, 'w', encoding='utf-8') as f:
        f.write(content)
    print('Route added to app.py')
else:
    print('Route already exists')
