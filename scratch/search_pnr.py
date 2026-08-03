import sys
with open(r'd:\GS\SYSTEM-FRD-Airline\templates\agent_dashboard.html', 'r', encoding='utf-8') as f:
    lines = f.readlines()
    for i, line in enumerate(lines):
        if 'switchTab(\'pnr\')' in line or 'switchTab("pnr")' in line:
            chunk = ''.join(lines[max(0, i-2):min(len(lines), i+60)])
            sys.stdout.buffer.write(chunk.encode('utf-8'))
            break
