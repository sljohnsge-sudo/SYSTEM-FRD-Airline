import os
import re

def update_file(path):
    with open(path, "r", encoding="utf-8") as f:
        content = f.read()

    # We need to replace the animation CSS blocks to make them fast
    
    # 1. Update the total animation time to 18s
    content = re.sub(r'animation: kenburns-crossfade \d+s infinite;', 'animation: kenburns-crossfade 18s infinite;', content)
    
    # 2. Update all animation delays
    content = re.sub(r'\.slide-1\s*{[^}]*animation-delay:\s*\d+s;[^}]*}', ".slide-1 {\n            background-image: url('https://images.unsplash.com/photo-1436491865332-7a61a109cc05?auto=format&fit=crop&w=2000&q=80');\n            animation-delay: 0s;\n        }", content)
    
    content = re.sub(r'\.slide-2\s*{[^}]*animation-delay:\s*\d+s;[^}]*}', ".slide-2 {\n            background-image: url('https://images.unsplash.com/photo-1494515843206-f3117d3a5d49?auto=format&fit=crop&w=2000&q=80');\n            animation-delay: 3s;\n        }", content)
    
    content = re.sub(r'\.slide-3\s*{[^}]*animation-delay:\s*\d+s;[^}]*}', ".slide-3 {\n            background-image: url('https://images.unsplash.com/photo-1507525428034-b723cf961d3e?auto=format&fit=crop&w=2000&q=80');\n            animation-delay: 6s;\n        }", content)
    
    content = re.sub(r'\.slide-4\s*{[^}]*animation-delay:\s*\d+s;[^}]*}', ".slide-4 {\n            background-image: url('https://images.unsplash.com/photo-1518066000714-58c45f1a2c0a?auto=format&fit=crop&w=2000&q=80');\n            animation-delay: 9s;\n        }", content)
    
    content = re.sub(r'\.slide-5\s*{[^}]*animation-delay:\s*\d+s;[^}]*}', ".slide-5 {\n            background-image: url('https://images.unsplash.com/photo-1499856871958-5b9627545d1a?auto=format&fit=crop&w=2000&q=80');\n            animation-delay: 12s;\n        }", content)
    
    content = re.sub(r'\.slide-6\s*{[^}]*animation-delay:\s*\d+s;[^}]*}', ".slide-6 {\n            background-image: url('https://images.unsplash.com/photo-1556745753-b2904692b3cd?auto=format&fit=crop&w=2000&q=80');\n            animation-delay: 15s;\n        }", content)
    
    # 3. Update the keyframes
    fast_keyframes = """@keyframes kenburns-crossfade {
            0% { opacity: 0; transform: scale(1.0); }
            5% { opacity: 1; }
            16.66% { opacity: 1; transform: scale(1.03); }
            22% { opacity: 0; transform: scale(1.05); }
            100% { opacity: 0; transform: scale(1.0); }
        }"""
    
    content = re.sub(r'@keyframes kenburns-crossfade\s*{[^}]*100%\s*{[^}]*}\s*}', fast_keyframes, content)

    with open(path, "w", encoding="utf-8") as f:
        f.write(content)

if __name__ == '__main__':
    update_file(r"c:\Users\SankaLasitha\OneDrive - Acorn\Desktop\SYSTEM FRD Airline\templates\welcome.html")
    update_file(r"c:\Users\SankaLasitha\OneDrive - Acorn\Desktop\SYSTEM FRD Airline\templates\login.html")
