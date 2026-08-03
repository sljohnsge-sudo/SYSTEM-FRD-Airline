filepath = r"d:\GS\SYSTEM-FRD-Airline\app.py"

with open(filepath, 'r', encoding='utf-8') as f:
    content = f.read()

# Find all route decorators containing bookings or flight or pnr
import re
routes = re.findall(r"@app\.route\(\"[^\"]+\"", content)
print("Routes in app.py:")
for r in routes:
    if "book" in r or "flight" in r or "pnr" in r or "agent" in r:
        print(r)
