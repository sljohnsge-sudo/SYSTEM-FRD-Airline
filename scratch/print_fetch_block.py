filepath = r"d:\GS\SYSTEM-FRD-Airline\static\js\main.js"

with open(filepath, 'r', encoding='utf-8') as f:
    content = f.read()

# Let's search for occurrences of 'resultsWrapper' or any querySelectors after the fetch
# We can find the fetch inside retrieveBookingByPNR and print the whole block after the fetch.
import re
match = re.search(r"fetch\(`/api/pnr/retrieve\?pnr=\$\{pnrCode\}`\)", content)
if match:
    start_pos = match.start()
    print("--- Fetch block code ---")
    print(content[start_pos : start_pos + 4000])
else:
    print("Fetch block not found")
