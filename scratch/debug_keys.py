with open(r'd:\GS\SYSTEM-FRD-Airline\app.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()

for i, line in enumerate(lines):
    if 'if "CatalogProductOfferingsResponse" in tp_data:' in line:
        lines.insert(i, '    print("Keys in tp_data app.py:", tp_data.keys() if isinstance(tp_data, dict) else type(tp_data))\n')
        break

with open(r'd:\GS\SYSTEM-FRD-Airline\app.py', 'w', encoding='utf-8') as f:
    f.writelines(lines)
