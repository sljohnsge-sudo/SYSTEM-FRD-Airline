filepath = r"d:\GS\SYSTEM-FRD-Airline\app.py"

with open(filepath, 'r', encoding='utf-8') as f:
    content = f.read()

idx = content.find('@app.route("/api/flights/book"')
if idx != -1:
    print(content[idx : idx + 3000])
else:
    print("Not found")
