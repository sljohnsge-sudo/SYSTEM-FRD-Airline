with open(r'd:\GS\SYSTEM-FRD-Airline\app.py', 'r', encoding='utf-8') as f:
    content = f.read()

target = 'if "user_id" not in session or session.get("role") != "admin":'
replacement = 'if "user_id" not in session or session.get("role") not in ["admin", "b2c_admin"]:'

# Only replace within the B2C section.
b2c_split = content.split('# B2C ADMIN PORTAL APIS')
if len(b2c_split) > 1:
    b2c_split[1] = b2c_split[1].replace(target, replacement)
    new_content = '# B2C ADMIN PORTAL APIS'.join(b2c_split)
    
    with open(r'd:\GS\SYSTEM-FRD-Airline\app.py', 'w', encoding='utf-8') as f:
        f.write(new_content)
    print("app.py updated for B2C roles.")
