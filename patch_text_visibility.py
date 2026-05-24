import os
import re

def update_file(path):
    with open(path, "r", encoding="utf-8") as f:
        content = f.read()

    # 1. Update the overlay to be slightly darker for better contrast
    content = re.sub(
        r'\.overlay\s*{[^}]*background:\s*linear-gradient\([^)]+\);[^}]*}',
        """.overlay {
            position: fixed;
            top: 0; left: 0; width: 100%; height: 100%;
            background: linear-gradient(135deg, rgba(136, 18, 59, 0.75) 0%, rgba(0, 59, 149, 0.85) 100%);
            z-index: -1;
        }""", content
    )

    # 2. Fix the hero-title so it's not a transparent gradient blending into the background!
    old_title_css = r'\.hero-title\s*{[^}]*background:\s*linear-gradient[^}]*-webkit-text-fill-color:\s*transparent;[^}]*}'
    new_title_css = """.hero-title {
            font-size: 56px;
            font-weight: 800;
            font-family: 'Outfit', sans-serif;
            line-height: 1.15;
            margin-bottom: 20px;
            max-width: 900px;
            color: #ffffff !important;
            text-shadow: 0 4px 25px rgba(0, 0, 0, 0.8), 0 2px 5px rgba(0,0,0,0.6);
            background: none !important;
            -webkit-text-fill-color: #ffffff !important;
        }"""
    if re.search(old_title_css, content):
        content = re.sub(old_title_css, new_title_css, content)
    else:
        # Just manually replace it if regex fails
        content = re.sub(r'\.hero-title\s*{[^}]+}', new_title_css, content)

    # 3. Fix hero-desc to be bright white with shadow
    new_desc_css = """.hero-desc {
            font-size: 19px;
            color: #ffffff !important;
            max-width: 650px;
            line-height: 1.6;
            margin-bottom: 40px;
            text-shadow: 0 4px 15px rgba(0, 0, 0, 0.8), 0 1px 3px rgba(0,0,0,0.6);
            font-weight: 500;
        }"""
    content = re.sub(r'\.hero-desc\s*{[^}]+}', new_desc_css, content)

    # 4. Fix feature cards text
    new_feature_h3 = """.feature-card h3 {
            font-size: 20px;
            margin-bottom: 12px;
            color: #ffffff !important;
            text-shadow: 0 2px 10px rgba(0,0,0,0.5);
            font-weight: 700;
        }"""
    content = re.sub(r'\.feature-card h3\s*{[^}]+}', new_feature_h3, content)

    new_feature_p = """.feature-card p {
            color: rgba(255, 255, 255, 0.95) !important;
            font-size: 15px;
            line-height: 1.6;
            text-shadow: 0 1px 5px rgba(0,0,0,0.4);
        }"""
    content = re.sub(r'\.feature-card p\s*{[^}]+}', new_feature_p, content)
    
    # 5. Fix Glassmorphic background for feature cards to ensure contrast
    new_feature_card = """.feature-card {
            background: rgba(0, 0, 0, 0.35) !important;
            backdrop-filter: blur(16px);
            -webkit-backdrop-filter: blur(16px);
            border: 1px solid rgba(255, 255, 255, 0.2) !important;
            border-radius: 20px;
            padding: 35px;
            transition: all 0.3s;
        }"""
    content = re.sub(r'\.feature-card\s*{[^}]*transition:[^}]*}', new_feature_card, content)

    with open(path, "w", encoding="utf-8") as f:
        f.write(content)

if __name__ == '__main__':
    update_file(r"c:\Users\SankaLasitha\OneDrive - Acorn\Desktop\SYSTEM FRD Airline\templates\welcome.html")
