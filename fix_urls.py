import os

def fix_url_for(path):
    with open(path, "r", encoding="utf-8") as f:
        content = f.read()

    content = content.replace("url_for('welcome')", "url_for('index')")

    with open(path, "w", encoding="utf-8") as f:
        f.write(content)

if __name__ == '__main__':
    fix_url_for(r"c:\Users\SankaLasitha\OneDrive - Acorn\Desktop\SYSTEM FRD Airline\app.py")
    fix_url_for(r"c:\Users\SankaLasitha\OneDrive - Acorn\Desktop\SYSTEM FRD Airline\templates\admin_dashboard.html")
    fix_url_for(r"c:\Users\SankaLasitha\OneDrive - Acorn\Desktop\SYSTEM FRD Airline\templates\agent_dashboard.html")
