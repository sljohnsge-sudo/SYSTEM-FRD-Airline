with open(r'd:\GS\SYSTEM-FRD-Airline\templates\login.html', 'r', encoding='utf-8') as f:
    html = f.read()

html = html.replace('ATL Admin / Agent Portal', 'ATL B2C Admin Portal')
html = html.replace('action="/login"', 'action="/b2c/admin/login"')
html = html.replace('Sign into your ATL Portal', 'Sign into B2C Admin Portal')

with open(r'd:\GS\SYSTEM-FRD-Airline\templates\b2c_admin_login.html', 'w', encoding='utf-8') as f:
    f.write(html)
print('Created b2c_admin_login.html')
