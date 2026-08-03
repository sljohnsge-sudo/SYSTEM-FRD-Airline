with open(r'd:\GS\SYSTEM-FRD-Airline\app.py', 'a', encoding='utf-8') as f:
    f.write("""

@app.route("/b2c/admin/login", methods=["GET", "POST"])
def b2c_admin_login():
    error = None
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")
        
        user = query_db("SELECT * FROM users WHERE username = %s AND password = %s AND role = 'b2c_admin'", (username, password), one=True)
        if user:
            if user.get("status") == "inactive":
                error = "Your account has been deactivated. Please contact support."
            else:
                session["user_id"] = user["id"]
                session["username"] = user["username"]
                session["role"] = user["role"]
                session["company_name"] = user["company_name"]
                
                return redirect(url_for("b2c_admin_dashboard"))
        else:
            error = "Invalid username or password for B2C Admin."
            
    return render_template("b2c_admin_login.html", error=error)

@app.route("/b2c/admin")
def b2c_admin_dashboard():
    if "user_id" not in session or session.get("role") != "b2c_admin":
        return redirect(url_for("b2c_admin_login"))
        
    admin_info = query_db("SELECT * FROM users WHERE id = %s", (session["user_id"],), one=True)
    return render_template("b2c_admin_dashboard.html", admin=admin_info)
""")
