filepath = r"d:\GS\SYSTEM-FRD-Airline\static\css\style.css"

with open(filepath, 'r', encoding='utf-8') as f:
    content = f.read()

import re
root_match = re.search(r":root\s*\{([^}]+)\}", content)
if root_match:
    print("CSS Root Variables:")
    print(root_match.group(1).strip())
else:
    print("No :root section found")
