import os
import re

def update_file(path):
    with open(path, "r", encoding="utf-8") as f:
        content = f.read()

    # Re-inject clouds and live-flights CSS
    css_to_add = """
        /* Dynamic Parallax Clouds */
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
            opacity: 0.25;
            filter: blur(20px);
            will-change: transform;
        }

        .css-cloud::before, .css-cloud::after {
            content: '';
            position: absolute;
            background: #ffffff;
            border-radius: 50%;
        }

        .c1 { width: 400px; height: 120px; top: 15%; animation: float-fast 18s linear infinite; }
        .c1::before { width: 180px; height: 180px; top: -80px; left: 50px; }
        .c1::after { width: 120px; height: 120px; top: -50px; right: 60px; }

        .c2 { width: 500px; height: 150px; top: 45%; animation: float-slow 35s linear infinite; animation-delay: -10s; opacity: 0.2; filter: blur(30px); }
        .c2::before { width: 220px; height: 220px; top: -100px; left: 70px; }
        .c2::after { width: 150px; height: 150px; top: -60px; right: 80px; }

        .c3 { width: 350px; height: 100px; top: 80%; animation: float-fast 22s linear infinite; animation-delay: -8s; }
        .c3::before { width: 150px; height: 150px; top: -70px; left: 40px; }
        .c3::after { width: 100px; height: 100px; top: -40px; right: 50px; }

        /* Live Flight Planes */
        .live-flight-container {
            position: fixed;
            top: 0; left: 0; width: 100%; height: 100%;
            z-index: 0;
            overflow: hidden;
            pointer-events: none;
        }

        .flying-plane {
            position: absolute;
            width: 120px;
            height: auto;
            opacity: 0.9;
            filter: drop-shadow(0 15px 15px rgba(0,0,0,0.3));
            will-change: transform;
        }

        .plane-1 { animation: fly-live-1 25s linear infinite; top: 20%; left: -20%; width: 180px; z-index: 2; }
        .plane-2 { animation: fly-live-2 40s linear infinite; animation-delay: -15s; top: 60%; left: -20%; width: 90px; opacity: 0.6; filter: blur(2px); z-index: 1; }
        .plane-3 { animation: fly-live-3 32s linear infinite; animation-delay: -5s; top: 10%; left: -20%; width: 110px; opacity: 0.8; filter: blur(1px); z-index: 1; }

        @keyframes fly-live-1 {
            0% { transform: translate(-20vw, 30vh) rotate(-10deg) scale(0.8); }
            100% { transform: translate(120vw, -30vh) rotate(-10deg) scale(1.1); }
        }

        @keyframes fly-live-2 {
            0% { transform: translate(-20vw, 10vh) rotate(-5deg) scale(0.5); }
            100% { transform: translate(120vw, -10vh) rotate(-5deg) scale(0.6); }
        }

        @keyframes fly-live-3 {
            0% { transform: translate(-20vw, -20vh) rotate(-8deg) scale(0.6); }
            100% { transform: translate(120vw, 20vh) rotate(-8deg) scale(0.7); }
        }
    """

    if "fly-live-1" not in content:
        content = content.replace("</style>", css_to_add + "\n</style>")

    # Re-inject HTML
    html_to_add = """
    <!-- Live Clouds & Planes -->
    <div class="clouds-container">
        <div class="css-cloud c1"></div>
        <div class="css-cloud c2"></div>
        <div class="css-cloud c3"></div>
    </div>
    
    <div class="live-flight-container">
        <!-- Plane 1 (Foreground) -->
        <svg class="flying-plane plane-1" viewBox="0 0 24 24" fill="#ffffff" xmlns="http://www.w3.org/2000/svg">
            <path d="M21.949 10.169l-7.391-2.923-3.69-7.227c-.201-.392-.614-.619-1.054-.619-.684 0-1.163.666-.998 1.332l1.637 6.549-5.111-2.022-1.921-3.201c-.161-.269-.452-.432-.765-.432-.614 0-1.042.597-.872 1.189l1.467 5.135L.302 9.07c-.19.075-.302.261-.302.464 0 .285.231.516.516.516h.001l2.949-.001 2.366 2.054-2.85 1.545c-.214.116-.347.337-.347.58 0 .37.301.671.671.671.109 0 .216-.027.311-.078l4.492-2.433 4.98 1.969-1.849 5.548c-.149.447.182.903.652.903.262 0 .506-.142.636-.376l3.99-7.182 6.812 2.694c.594.235 1.258-.056 1.493-.65.235-.595-.055-1.259-.65-1.494z"/>
        </svg>
        
        <!-- Plane 2 (Background) -->
        <svg class="flying-plane plane-2" viewBox="0 0 24 24" fill="#ffffff" xmlns="http://www.w3.org/2000/svg">
            <path d="M21.949 10.169l-7.391-2.923-3.69-7.227c-.201-.392-.614-.619-1.054-.619-.684 0-1.163.666-.998 1.332l1.637 6.549-5.111-2.022-1.921-3.201c-.161-.269-.452-.432-.765-.432-.614 0-1.042.597-.872 1.189l1.467 5.135L.302 9.07c-.19.075-.302.261-.302.464 0 .285.231.516.516.516h.001l2.949-.001 2.366 2.054-2.85 1.545c-.214.116-.347.337-.347.58 0 .37.301.671.671.671.109 0 .216-.027.311-.078l4.492-2.433 4.98 1.969-1.849 5.548c-.149.447.182.903.652.903.262 0 .506-.142.636-.376l3.99-7.182 6.812 2.694c.594.235 1.258-.056 1.493-.65.235-.595-.055-1.259-.65-1.494z"/>
        </svg>

        <!-- Plane 3 (Background 2) -->
        <svg class="flying-plane plane-3" viewBox="0 0 24 24" fill="#ffffff" xmlns="http://www.w3.org/2000/svg">
            <path d="M21.949 10.169l-7.391-2.923-3.69-7.227c-.201-.392-.614-.619-1.054-.619-.684 0-1.163.666-.998 1.332l1.637 6.549-5.111-2.022-1.921-3.201c-.161-.269-.452-.432-.765-.432-.614 0-1.042.597-.872 1.189l1.467 5.135L.302 9.07c-.19.075-.302.261-.302.464 0 .285.231.516.516.516h.001l2.949-.001 2.366 2.054-2.85 1.545c-.214.116-.347.337-.347.58 0 .37.301.671.671.671.109 0 .216-.027.311-.078l4.492-2.433 4.98 1.969-1.849 5.548c-.149.447.182.903.652.903.262 0 .506-.142.636-.376l3.99-7.182 6.812 2.694c.594.235 1.258-.056 1.493-.65.235-.595-.055-1.259-.65-1.494z"/>
        </svg>
    </div>
    """

    if "live-flight-container" not in content:
        content = content.replace('<div class="overlay"></div>', html_to_add + '\n    <div class="overlay"></div>')

    with open(path, "w", encoding="utf-8") as f:
        f.write(content)

if __name__ == '__main__':
    update_file(r"c:\Users\SankaLasitha\OneDrive - Acorn\Desktop\SYSTEM FRD Airline\templates\welcome.html")
    update_file(r"c:\Users\SankaLasitha\OneDrive - Acorn\Desktop\SYSTEM FRD Airline\templates\login.html")
