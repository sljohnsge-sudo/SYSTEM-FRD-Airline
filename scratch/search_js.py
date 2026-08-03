import re

filepath = r"d:\GS\SYSTEM-FRD-Airline\static\js\main.js"

# Read with various encodings
for encoding in ['utf-8', 'utf-16', 'utf-16-le', 'utf-16-be', 'latin-1']:
    try:
        with open(filepath, 'r', encoding=encoding) as f:
            content = f.read()
        print(f"Successfully read with {encoding}")
        break
    except UnicodeDecodeError:
        continue
else:
        print("Could not decode file")
        exit(1)

# Find all lines containing "split"
lines = content.splitlines()
print("\n--- Searching for 'split' ---")
for idx, line in enumerate(lines):
    if "split" in line:
        print(f"Line {idx+1}: {line.strip()}")

print("\n--- Searching for 'flight_number' ---")
for idx, line in enumerate(lines):
    if "flight_number" in line:
        # Just print first 10 matches or summary
        print(f"Line {idx+1}: {line.strip()}")
