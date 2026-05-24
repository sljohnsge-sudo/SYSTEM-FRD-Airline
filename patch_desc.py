import os
import re

def update_file(path):
    with open(path, "r", encoding="utf-8") as f:
        content = f.read()

    new_desc_css = """.hero-desc {
            font-size: 24px;
            color: #ffffff !important;
            max-width: 850px;
            line-height: 1.6;
            margin-bottom: 45px;
            text-shadow: 0 4px 15px rgba(0, 0, 0, 1), 0 2px 5px rgba(0,0,0,0.8), 0 0 30px rgba(0,0,0,0.6);
            font-weight: 700;
            background: none !important;
            backdrop-filter: none;
            padding: 0;
            border: none;
            box-shadow: none;
            letter-spacing: 0.5px;
        }"""
        
    content = re.sub(r'\.hero-desc\s*{[^}]+}', new_desc_css, content)

    with open(path, "w", encoding="utf-8") as f:
        f.write(content)

if __name__ == '__main__':
    update_file(r"c:\Users\SankaLasitha\OneDrive - Acorn\Desktop\SYSTEM FRD Airline\templates\welcome.html")
