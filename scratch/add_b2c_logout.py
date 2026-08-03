with open(r'd:\GS\SYSTEM-FRD-Airline\app.py', 'r', encoding='utf-8') as f:
    content = f.read()

parts = content.split('if __name__ == ')
new_route = '''
@app.route("/b2c/admin/logout")
def b2c_admin_logout():
    session.clear()
    return redirect(url_for("b2c_admin_login"))

'''
new_content = parts[0] + new_route + 'if __name__ == ' + parts[1]

with open(r'd:\GS\SYSTEM-FRD-Airline\app.py', 'w', encoding='utf-8') as f:
    f.write(new_content)
