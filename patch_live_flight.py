import os

def update_file(path):
    with open(path, "r", encoding="utf-8") as f:
        content = f.read()

    css_inject = """
        /* Live Flight Planes */
        .live-flight-container {
            position: fixed;
            top: 0; left: 0; width: 100%; height: 100%;
            z-index: -1;
            pointer-events: none;
            overflow: hidden;
        }
        
        .live-plane {
            position: absolute;
            color: #ffffff;
            filter: drop-shadow(0 15px 25px rgba(0, 0, 0, 0.3));
            will-change: transform;
        }

        @keyframes fly-live-1 {
            0% { transform: translate(-20vw, 80vh) rotate(-15deg); }
            100% { transform: translate(120vw, -20vh) rotate(-15deg); }
        }
        
        @keyframes fly-live-2 {
            0% { transform: translate(-10vw, 60vh) rotate(-10deg) scale(0.6); }
            100% { transform: translate(120vw, 10vh) rotate(-10deg) scale(0.6); }
        }
        
        @keyframes fly-live-3 {
            0% { transform: translate(-10vw, 40vh) rotate(-5deg) scale(0.3); }
            100% { transform: translate(120vw, 30vh) rotate(-5deg) scale(0.3); }
        }
    """
    
    html_inject = """
    <div class="live-flight-container">
        <i class="fa-solid fa-plane live-plane" style="animation: fly-live-1 25s linear infinite; font-size: 160px; opacity: 0.6; animation-delay: 0s;"></i>
        <i class="fa-solid fa-plane live-plane" style="animation: fly-live-2 35s linear infinite; font-size: 160px; opacity: 0.4; animation-delay: -10s;"></i>
        <i class="fa-solid fa-plane live-plane" style="animation: fly-live-3 45s linear infinite; font-size: 160px; opacity: 0.2; animation-delay: -25s;"></i>
    </div>
    """
    
    # 1. Update CSS
    if ".live-flight-container {" not in content:
        content = content.replace(".clouds-container {", css_inject + "\n        .clouds-container {")

    # 2. Update HTML
    if "live-flight-container" not in content:
        content = content.replace('<div class="clouds-container">', html_inject + '\n    <div class="clouds-container">')

    with open(path, "w", encoding="utf-8") as f:
        f.write(content)

if __name__ == '__main__':
    update_file(r"c:\Users\SankaLasitha\OneDrive - Acorn\Desktop\SYSTEM FRD Airline\templates\welcome.html")
    update_file(r"c:\Users\SankaLasitha\OneDrive - Acorn\Desktop\SYSTEM FRD Airline\templates\login.html")
