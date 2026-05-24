import os

def update_file(path):
    with open(path, "r", encoding="utf-8") as f:
        content = f.read()

    css_inject = """
        /* Dynamic Parallax Clouds & Flight Animation */
        body {
            background-size: 110% 110%; /* Extra size for panning */
            animation: plane-bobbing 6s ease-in-out infinite;
        }

        @keyframes plane-bobbing {
            0% { background-position: 50% 50%; }
            50% { background-position: 50% 53%; }
            100% { background-position: 50% 50%; }
        }

        .clouds-container {
            position: fixed;
            top: 0; left: 0; width: 100%; height: 100%;
            z-index: -1;
            overflow: hidden;
            pointer-events: none;
        }

        @keyframes float-fast {
            0% { transform: translateX(110vw); }
            100% { transform: translateX(-50vw); }
        }
        
        @keyframes float-slow {
            0% { transform: translateX(110vw); }
            100% { transform: translateX(-50vw); }
        }

        .css-cloud {
            position: absolute;
            background: #ffffff;
            border-radius: 200px;
            opacity: 0.15;
            filter: blur(25px);
            will-change: transform;
        }

        .css-cloud::before, .css-cloud::after {
            content: '';
            position: absolute;
            background: #ffffff;
            border-radius: 50%;
        }

        .c1 {
            width: 400px; height: 120px;
            top: 15%; animation: float-fast 18s linear infinite;
        }
        .c1::before { width: 180px; height: 180px; top: -80px; left: 50px; }
        .c1::after { width: 120px; height: 120px; top: -50px; right: 60px; }

        .c2 {
            width: 500px; height: 150px;
            top: 45%; animation: float-slow 35s linear infinite; animation-delay: -10s;
            opacity: 0.12; filter: blur(35px);
        }
        .c2::before { width: 220px; height: 220px; top: -100px; left: 70px; }
        .c2::after { width: 150px; height: 150px; top: -60px; right: 80px; }

        .c3 {
            width: 350px; height: 100px;
            top: 80%; animation: float-fast 22s linear infinite; animation-delay: -8s;
        }
        .c3::before { width: 150px; height: 150px; top: -70px; left: 40px; }
        .c3::after { width: 100px; height: 100px; top: -40px; right: 50px; }
        
        .c4 {
            width: 600px; height: 160px;
            top: 5%; animation: float-slow 40s linear infinite; animation-delay: -20s;
            opacity: 0.1; filter: blur(40px);
        }
        .c4::before { width: 250px; height: 250px; top: -110px; left: 80px; }
        .c4::after { width: 180px; height: 180px; top: -70px; right: 90px; }
    """
    
    html_inject = """
    <div class="clouds-container">
        <div class="css-cloud c1"></div>
        <div class="css-cloud c2"></div>
        <div class="css-cloud c3"></div>
        <div class="css-cloud c4"></div>
    </div>
    """
    
    # 1. Update CSS
    if "plane-bobbing" not in content:
        # Replace background-size: cover; with our new CSS block
        content = content.replace("background-size: cover;", css_inject)

    # 2. Update HTML
    if "clouds-container" not in content:
        content = content.replace('<div class="overlay"></div>', '<div class="overlay"></div>\n' + html_inject)

    with open(path, "w", encoding="utf-8") as f:
        f.write(content)

if __name__ == '__main__':
    update_file(r"c:\Users\SankaLasitha\OneDrive - Acorn\Desktop\SYSTEM FRD Airline\templates\welcome.html")
    update_file(r"c:\Users\SankaLasitha\OneDrive - Acorn\Desktop\SYSTEM FRD Airline\templates\login.html")
