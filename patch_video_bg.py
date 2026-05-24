import os

def update_file(path):
    with open(path, "r", encoding="utf-8") as f:
        content = f.read()

    # Replace the old video ID with the new one
    content = content.replace("Uqc6X728pTU", "7CoRyx9SEC0")

    with open(path, "w", encoding="utf-8") as f:
        f.write(content)

if __name__ == '__main__':
    update_file(r"c:\Users\SankaLasitha\OneDrive - Acorn\Desktop\SYSTEM FRD Airline\templates\welcome.html")
    update_file(r"c:\Users\SankaLasitha\OneDrive - Acorn\Desktop\SYSTEM FRD Airline\templates\login.html")
