import os
import re

def fix_jinja_syntax(path):
    with open(path, "r", encoding="utf-8") as f:
        content = f.read()

    # Replace the incorrectly escaped url_for(\'index\') with url_for('index')
    content = content.replace(r"{{ url_for(\'index\') }}", "{{ url_for('index') }}")

    with open(path, "w", encoding="utf-8") as f:
        f.write(content)

if __name__ == '__main__':
    fix_jinja_syntax(r"c:\Users\SankaLasitha\OneDrive - Acorn\Desktop\SYSTEM FRD Airline\templates\admin_dashboard.html")
    fix_jinja_syntax(r"c:\Users\SankaLasitha\OneDrive - Acorn\Desktop\SYSTEM FRD Airline\templates\agent_dashboard.html")
