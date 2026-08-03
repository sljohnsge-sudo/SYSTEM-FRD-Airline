import os

search_term = "function retrieveBookingByPNR"
found_files = []

for root, dirs, files in os.walk("."):
    for file in files:
        if file.endswith(('.js', '.html', '.py')):
            filepath = os.path.join(root, file)
            try:
                with open(filepath, 'r', encoding='utf-8') as f:
                    content = f.read()
                if search_term in content:
                    found_files.append(filepath)
            except Exception:
                pass

print("Files containing search term:")
for f in found_files:
    print(f)
