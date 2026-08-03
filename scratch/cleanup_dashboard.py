with open(r'd:\GS\SYSTEM-FRD-Airline\templates\admin_dashboard.html', 'r', encoding='utf-8') as f:
    html = f.read()

# Remove the sidebar B2C section
sidebar_start = html.find('<div style="font-size: 11px; text-transform: uppercase; color: rgba(255,255,255,0.5); margin-bottom: 5px; padding-left: 20px; font-weight: bold;">B2C Configuration</div>')
if sidebar_start != -1:
    div_start = html.rfind('<div', 0, sidebar_start)
    div_end = html.find('</div>\n                <div style="margin-top: 10px; border-top: 1px solid rgba(255,255,255,0.1); padding-top: 15px;">', div_start)
    if div_end != -1:
        # replace the whole block back to original
        original = '''<div style="margin-top: 15px; border-top: 1px solid rgba(255,255,255,0.1); padding-top: 15px;">
                    <a href="{{ url_for('index') }}" class="menu-item">'''
        html = html[:div_start] + original + html[div_end + len('</div>\n                <div style="margin-top: 10px; border-top: 1px solid rgba(255,255,255,0.1); padding-top: 15px;">\n                    <a href="{{ url_for(\'index\') }}" class="menu-item">'):]

# Remove the B2C Tabs
b2c_tab_start = html.find('<!-- ========================================================= -->\n            <!-- TAB: B2C USERS -->')
if b2c_tab_start != -1:
    b2c_tab_end = html.find('<!-- Modals -->', b2c_tab_start)
    if b2c_tab_end != -1:
        html = html[:b2c_tab_start] + html[b2c_tab_end:]

with open(r'd:\GS\SYSTEM-FRD-Airline\templates\admin_dashboard.html', 'w', encoding='utf-8') as f:
    f.write(html)
print("admin_dashboard.html cleaned up.")
