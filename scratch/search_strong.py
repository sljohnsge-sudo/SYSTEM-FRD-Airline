filepath = r"d:\GS\SYSTEM-FRD-Airline\static\css\style.css"

with open(filepath, 'r', encoding='utf-8') as f:
    content = f.read()

import re
matches = [m.start() for m in re.finditer(r"strong", content, re.IGNORECASE)]
print(f"Found {len(matches)} strong occurrences in style.css")
