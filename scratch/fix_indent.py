with open(r'd:\GS\SYSTEM-FRD-Airline\app.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()

lines[1049] = '            except Exception as e:\n'
lines[1050] = '                print("Error parsing flight:", e)\n'

with open(r'd:\GS\SYSTEM-FRD-Airline\app.py', 'w', encoding='utf-8') as f:
    f.writelines(lines)
