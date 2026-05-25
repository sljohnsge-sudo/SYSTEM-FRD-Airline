import os
import re

def update_dashboard(path, role):
    with open(path, "r", encoding="utf-8") as f:
        content = f.read()

    # 1. Remove the old buttons from the sidebar-footer
    old_buttons_regex = r'<a href="\{\{\s*url_for\(\'index\'\)\s*\}\}"[^>]*>.*?</a>\s*<a href="\{\{\s*url_for\(\'logout\'\)\s*\}\}"[^>]*>.*?</a>'
    content = re.sub(old_buttons_regex, '', content, flags=re.DOTALL)
    
    # Also handle if they were separated or formatted differently
    content = re.sub(r'<a href="\{\{\s*url_for\(\'index\'\)\s*\}\}" class="btn-logout".*?</a>', '', content, flags=re.DOTALL)
    content = re.sub(r'<a href="\{\{\s*url_for\(\'logout\'\)\s*\}\}" class="btn-logout".*?</a>', '', content, flags=re.DOTALL)

    # 2. Append the buttons at the bottom of the sidebar-menu
    new_buttons = """
                <div style="margin-top: 15px; border-top: 1px solid rgba(255,255,255,0.1); padding-top: 15px;">
                    <a href="{{ url_for('index') }}" class="menu-item">
                        <i class="fa-solid fa-house"></i>
                        <span>Back to Main Page</span>
                    </a>
                    <a href="{{ url_for('logout') }}" class="menu-item" style="color: #ff6b6b;">
                        <i class="fa-solid fa-right-from-bracket"></i>
                        <span>Logout Account</span>
                    </a>
                </div>
            </nav>"""
            
    content = content.replace("</nav>", new_buttons)

    with open(path, "w", encoding="utf-8") as f:
        f.write(content)

if __name__ == '__main__':
    update_dashboard(r"c:\Users\SankaLasitha\OneDrive - Acorn\Desktop\SYSTEM FRD Airline\templates\admin_dashboard.html", "admin")
    update_dashboard(r"c:\Users\SankaLasitha\OneDrive - Acorn\Desktop\SYSTEM FRD Airline\templates\agent_dashboard.html", "agent")
