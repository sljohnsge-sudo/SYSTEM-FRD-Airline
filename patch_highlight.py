import os
import re

def update_file(path):
    with open(path, "r", encoding="utf-8") as f:
        content = f.read()

    # 1. Fix the hero-badge to be bright and highly visible
    new_badge_css = """.hero-badge {
            background: rgba(255, 255, 255, 0.15) !important;
            backdrop-filter: blur(10px);
            border: 1px solid rgba(255, 255, 255, 0.6) !important;
            color: #ffffff !important;
            padding: 8px 22px;
            border-radius: 30px;
            font-size: 14px;
            font-weight: 700;
            margin-bottom: 25px;
            letter-spacing: 1px;
            text-transform: uppercase;
            box-shadow: 0 0 20px rgba(255, 255, 255, 0.2);
            text-shadow: 0 2px 5px rgba(0,0,0,0.8);
        }"""
    
    # 2. Fix the hero-desc to be highlighted inside a glass box with larger text
    new_desc_css = """.hero-desc {
            font-size: 20px;
            color: #ffffff !important;
            max-width: 750px;
            line-height: 1.7;
            margin-bottom: 45px;
            text-shadow: 0 2px 8px rgba(0, 0, 0, 0.8);
            font-weight: 600;
            background: rgba(0, 0, 0, 0.45);
            backdrop-filter: blur(12px);
            padding: 22px 35px;
            border-radius: 15px;
            border: 1px solid rgba(255, 255, 255, 0.25);
            box-shadow: 0 15px 35px rgba(0,0,0,0.4);
            letter-spacing: 0.5px;
        }"""
        
    # Replace the old CSS in the <style> block
    if re.search(r'\.hero-badge\s*{[^}]+}', content):
        content = re.sub(r'\.hero-badge\s*{[^}]+}', new_badge_css, content)
        
    if re.search(r'\.hero-desc\s*{[^}]+}', content):
        content = re.sub(r'\.hero-desc\s*{[^}]+}', new_desc_css, content)

    with open(path, "w", encoding="utf-8") as f:
        f.write(content)

if __name__ == '__main__':
    update_file(r"c:\Users\SankaLasitha\OneDrive - Acorn\Desktop\SYSTEM FRD Airline\templates\welcome.html")
