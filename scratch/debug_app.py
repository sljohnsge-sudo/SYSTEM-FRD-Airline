with open(r'd:\GS\SYSTEM-FRD-Airline\app.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()

for i, line in enumerate(lines):
    if 'offerings = root.get(' in line and 'CatalogProductOffering' in line:
        lines.insert(i+1, '        print("Offerings count:", len(offerings))\n')
        break

with open(r'd:\GS\SYSTEM-FRD-Airline\app.py', 'w', encoding='utf-8') as f:
    f.writelines(lines)
