import os
import re

def update_app_py(path):
    with open(path, "r", encoding="utf-8") as f:
        content = f.read()

    # Add the logout route if it doesn't exist
    if "@app.route('/logout')" not in content:
        logout_route = """
@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('welcome'))
"""
        # Inject it right before the first @app.route('/login') or at the end
        if "@app.route('/login', methods=['GET', 'POST'])" in content:
            content = content.replace("@app.route('/login', methods=['GET', 'POST'])", logout_route + "\n@app.route('/login', methods=['GET', 'POST'])")
        else:
            content += logout_route
            
        with open(path, "w", encoding="utf-8") as f:
            f.write(content)

def update_dashboard(path):
    with open(path, "r", encoding="utf-8") as f:
        content = f.read()

    # Find the sidebar footer and add the "Back to Main Page" button before the Logout button
    if "Back to Main Page" not in content:
        new_buttons = """
                <a href="{{ url_for('welcome') }}" class="btn-logout" style="background: rgba(255, 255, 255, 0.1); margin-bottom: 10px; color: #fff;">
                    <i class="fa-solid fa-house"></i>
                    <span>Back to Main Page</span>
                </a>
                <a href="{{ url_for('logout') }}" class="btn-logout">
"""
        content = content.replace("""<a href="{{ url_for('logout') }}" class="btn-logout">""", new_buttons)
        
        with open(path, "w", encoding="utf-8") as f:
            f.write(content)

if __name__ == '__main__':
    update_app_py(r"c:\Users\SankaLasitha\OneDrive - Acorn\Desktop\SYSTEM FRD Airline\app.py")
    update_dashboard(r"c:\Users\SankaLasitha\OneDrive - Acorn\Desktop\SYSTEM FRD Airline\templates\admin_dashboard.html")
    update_dashboard(r"c:\Users\SankaLasitha\OneDrive - Acorn\Desktop\SYSTEM FRD Airline\templates\agent_dashboard.html")
