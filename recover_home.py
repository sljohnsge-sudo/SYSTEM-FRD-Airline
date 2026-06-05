import re

with open("d:\\GS\\SYSTEM-FRD-Airline\\match_tab_366.txt", 'r', encoding='utf-8') as f:
    content = f.read()

# Let's find "B2C Hotel Search and Booking Javascript" or "function switchB2CTab"
# and get everything from there up to the end of the script block (which is before the closing </script>)
start_idx = content.find("function switchB2CTab")
if start_idx == -1:
    start_idx = content.find("switchB2CTab")

if start_idx != -1:
    sub = content[start_idx:start_idx+15000]
    # Let's clean up line numbers like "932: " or "1096:\n"
    # The format is "number: code_line" or "number:\ncode_line"
    cleaned = []
    lines = sub.split('\n')
    for line in lines:
        # Regex to strip "123: " or just "123:" at the beginning of a line
        m = re.match(r'^\s*\d+:\s*(.*)', line)
        if m:
            cleaned.append(m.group(1))
        else:
            cleaned.append(line)
            
    with open("d:\\GS\\SYSTEM-FRD-Airline\\recovered_b2c_js.js", 'w', encoding='utf-8') as out:
        out.write('\n'.join(cleaned))
    print("Wrote cleaned JS to recovered_b2c_js.js")
else:
    print("Could not find start index")
