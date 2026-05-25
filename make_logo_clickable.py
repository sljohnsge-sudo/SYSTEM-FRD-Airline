import os
import re

def update_brand_logo(path):
    with open(path, "r", encoding="utf-8") as f:
        content = f.read()

    # Find the sidebar-brand div
    match = re.search(r'(<div class="sidebar-brand"[^>]*>.*?</div>)', content, flags=re.DOTALL)
    if match:
        old_brand_html = match.group(1)
        
        # If it doesn't already have an onclick or href
        if 'onclick=' not in old_brand_html and 'href=' not in old_brand_html:
            # We add onclick, cursor: pointer, and some hover transition
            if 'style="' in old_brand_html:
                new_brand_html = old_brand_html.replace(
                    '<div class="sidebar-brand"', 
                    '<div class="sidebar-brand" onclick="window.location.href=\'{{ url_for(\\\'index\\\') }}\'" style="cursor: pointer; transition: opacity 0.2s;" onmouseover="this.style.opacity=0.8" onmouseout="this.style.opacity=1" '
                )
            else:
                new_brand_html = old_brand_html.replace(
                    '<div class="sidebar-brand">', 
                    '<div class="sidebar-brand" onclick="window.location.href=\'{{ url_for(\\\'index\\\') }}\'" style="cursor: pointer; transition: opacity 0.2s;" onmouseover="this.style.opacity=0.8" onmouseout="this.style.opacity=1">'
                )
                
            content = content.replace(old_brand_html, new_brand_html)
            
            with open(path, "w", encoding="utf-8") as f:
                f.write(content)

if __name__ == '__main__':
    update_brand_logo(r"c:\Users\SankaLasitha\OneDrive - Acorn\Desktop\SYSTEM FRD Airline\templates\admin_dashboard.html")
    update_brand_logo(r"c:\Users\SankaLasitha\OneDrive - Acorn\Desktop\SYSTEM FRD Airline\templates\agent_dashboard.html")
